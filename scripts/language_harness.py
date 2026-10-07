#!/usr/bin/env python3
"""Phase 2: equivalent-task execution and retained schema 2.0.0 evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import selectors
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from validate_phase1 import load_json

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "harness/tasks/bounded-integer-fold"
SOURCES = ROOT / "harness/implementations"
VERSION = "1.0.0"
FROZEN_SUITE_SHA256 = "3aaada34b7017e1056f1f4129a24d3d0ab7ca43041f8796421ceb04df850d32d"
TRUSTED_RECORD_CONTRACTS = {
    "https://github.com/QSOLKCB/CONSTRAINT-SHIFT/schema/v2.0.0/experiment-record.schema.json":
        ("6e0bc5adbffc9366bc16971a3c49d320900da3b2e9fe54a5ee70d46eb26b9581",
         "368a8138f09b63e08d857aeda8ede2459aac4057fc288d4e9e1275b78f9f93ba"),
    "https://github.com/QSOLKCB/CONSTRAINT-SHIFT/schema/harness-smoke-2.0.0.schema.json":
        ("2b2260dd9a80ea49d0b59a63b807bb70a3ddf490120dfd4bd3376ab354b2685f",
         "368a8138f09b63e08d857aeda8ede2459aac4057fc288d4e9e1275b78f9f93ba"),
}
ADAPTERS = {
    "c": ("C", "main.c", "gcc", ["--version"], ["-std=c11", "-O0", "-Wall", "-Wextra", "-Werror"]),
    "cpp": ("C++", "main.cpp", "g++", ["--version"], ["-std=c++17", "-O0", "-Wall", "-Wextra", "-Werror"]),
    "rust": ("Rust", "main.rs", "rustc", ["--version"], ["--edition=2021", "-C", "opt-level=0"]),
    "go": ("Go", "main.go", "go", ["version"], ["build"]),
    "python": ("Python", "main.py", "python3", ["--version"], ["-I", "-B"]),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def resolve_tool(language: str) -> str | None:
    return sys.executable if language == "python" else shutil.which(ADAPTERS[language][2])


def load_cases(path: Path) -> list[dict]:
    suite = load_json(path)
    if not isinstance(suite, dict) or set(suite) != {"task_id", "task_version", "cases"}:
        raise ValueError("invalid task suite")
    if suite["task_id"] != "TASK-FOLD-001" or suite["task_version"] != "1.0.0":
        raise ValueError("unsupported task contract")
    cases = suite["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("acceptance suite must be nonempty")
    ids = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "input", "expected"}:
            raise ValueError("invalid acceptance case")
        if not all(isinstance(case[k], str) for k in case) or not case["id"]:
            raise ValueError("case fields must be nonempty identifiers and strings")
        case["input"].encode("ascii")
        case["expected"].encode("ascii")
        tokens = case["input"].split()
        # Only decimal integers and ASCII whitespace belong to this input domain.
        if (not tokens or re.fullmatch(r"[+\-0-9 \t\n\r\f\v]+", case["input"]) is None
                or any(re.fullmatch(r"[+-]?[0-9]+", token) is None for token in tokens)):
            raise ValueError("case input is not decimal integer text")
        values = [int(t) for t in tokens]
        n, xs = values[0], values[1:]
        if not 0 <= n <= 64 or len(xs) != n or any(abs(x) > 1000 for x in xs):
            raise ValueError("case outside the bounded integer task")
        expected = f"{n} {sum(xs)} {sum(x * x for x in xs)}\n"
        if case["expected"] != expected:
            raise ValueError("acceptance oracle disagrees with frozen task")
        ids.append(case["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("case IDs must be unique")
    canonical = json.dumps(suite, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != FROZEN_SUITE_SHA256:
        raise ValueError("frozen suite count, IDs, order, or contents changed without a task version")
    return cases


def retained_record_contract(common: Path):
    """Use retained validation only after matching repository-approved identities.

    Unknown bundled code is never executed. Compile the checked bytes themselves
    so replacement of a file after the hash check cannot change executed code.
    """
    schema_bytes = (common / "schema.json").read_bytes()
    validator_path = common / "validate_phase1.py"
    validator_bytes = validator_path.read_bytes()
    schema = json.loads(schema_bytes)
    approved = TRUSTED_RECORD_CONTRACTS.get(schema.get("$id"))
    actual = (hashlib.sha256(schema_bytes).hexdigest(), hashlib.sha256(validator_bytes).hexdigest())
    if actual != approved:
        raise ValueError("retained record contract is not a registered trusted schema/validator")
    namespace = {"__name__": "retained_phase1_validator", "__file__": str(validator_path)}
    exec(compile(validator_bytes, str(validator_path), "exec"), namespace)
    return namespace["validate_record"], schema


def execute(argv: list[str], cwd: Path, stdin: bytes, timeout: float,
            output_limit: int, env: dict[str, str]) -> dict:
    """Bound captured output and the whole process group, without a shell."""
    if (not isinstance(argv, list) or not argv
            or any(not isinstance(argument, str) or "\0" in argument for argument in argv)
            or not Path(argv[0]).is_absolute()):
        raise ValueError("execution requires a nonempty string argv list with an absolute executable")
    argv = list(argv)
    started = time.monotonic_ns()
    result = {"argv": argv, "status": "error", "returncode": None,
              "stdout": b"", "stderr": b""}
    try:
        # Audited boundary: fixed adapter commands select resolved tools or the
        # built binary; paths/arguments remain separate literal tokens. Candidate
        # execution is intentional. This is process control, not a sandbox.
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=True, shell=False)
    except OSError as exc:
        result["error"] = str(exc)
        result["elapsed_ns"] = time.monotonic_ns() - started
        return result
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        assert child.stdin is not None
        try:
            child.stdin.write(stdin)
        except BrokenPipeError:
            pass
        finally:
            try:
                child.stdin.close()
            except BrokenPipeError:
                pass
        with selectors.DefaultSelector() as selector:
            for name in buffers:
                stream = getattr(child, name)
                selector.register(stream, selectors.EVENT_READ, name)
            result["status"] = "completed"
            deadline = time.monotonic() + timeout
            while selector.get_map() or child.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    result["status"] = "timeout"
                    break
                for key, _ in selector.select(min(remaining, 0.05)):
                    chunk = os.read(key.fileobj.fileno(), 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    buffer = buffers[key.data]
                    room = output_limit - sum(len(b) for b in buffers.values())
                    buffer.extend(chunk[:room])
                    if len(chunk) > room:
                        result["status"] = "output_limit"
                        break
                if result["status"] != "completed":
                    break
    finally:
        # Clean up descendants even when the direct process has already exited.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait()
        for stream in (child.stdout, child.stderr):
            if stream is not None:
                stream.close()
    result.update({name: bytes(data) for name, data in buffers.items()})
    result["returncode"] = child.returncode
    result["elapsed_ns"] = time.monotonic_ns() - started
    return result


def save_execution(directory: Path, name: str, result: dict) -> dict:
    envelope = dict(result)
    for stream in ("stdout", "stderr"):
        filename = f"{name}.{stream}.bin"
        (directory / filename).write_bytes(envelope.pop(stream))
        envelope[f"{stream}_file"] = filename
    write_json(directory / f"{name}.json", envelope)
    return envelope


def passed(result: dict) -> bool:
    return result["status"] == "completed" and result["returncode"] == 0


def failure_status(result: dict) -> str:
    return {"timeout": "timeout", "error": "invalid"}.get(result["status"], "failure")


def verification_failure(result: dict) -> str:
    return "error" if result["status"] in ("timeout", "error") else "fail"


def retained_verification_statuses(directory: Path, result: dict) -> dict:
    def streams(execution):
        contents = []
        for stream in ("stdout", "stderr"):
            filename = execution[f"{stream}_file"]
            if not isinstance(filename, str) or Path(filename).name != filename:
                raise ValueError("invalid retained stream filename")
            contents.append((directory / filename).read_bytes())
        return contents

    version, build, cases = result["version"], result["build"], result["cases"]
    version_status = "error"
    if version is not None:
        if version["status"] == "output_limit":
            version_status = "fail"
        elif passed(version) and any(content.strip() for content in streams(version)):
            version_status = "pass"
    build_status = "not_run" if build is None else (
        "pass" if passed(build) and not any(streams(build)) else verification_failure(build))
    test_status = "not_run" if not cases else (
        "pass" if all(case["accepted"] for case in cases) and not result["cases_not_run"]
        else verification_failure(cases[-1]))
    return {"toolchain-identity": version_status, "build": build_status, "frozen-cases": test_status}


def commands(language: str, tool: str, source: Path, binary: Path) -> tuple[list[str], list[str]]:
    flags = ADAPTERS[language][4]
    if language == "python":
        return ([tool, *flags, "-c", "import sys; compile(open(sys.argv[1], 'rb').read(), sys.argv[1], 'exec')", str(source)],
                [tool, *flags, str(source)])
    if language == "go":
        return [tool, *flags, "-o", str(binary), str(source)], [str(binary)]
    return [tool, *flags, str(source), "-o", str(binary)], [str(binary)]


def evidence_entry(path: Path, evidence_id: str, kind: str) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"evidence_id": evidence_id, "kind": kind,
            "path": path.relative_to(ROOT).as_posix(), "sha256": digest.hexdigest(),
            "bytes": size, "media_type": "application/octet-stream"}


def run_harness(languages: list[str], output: Path, sources: Path = SOURCES,
                timeout: float = 30.0, output_limit: int = 1048576) -> dict:
    with tempfile.TemporaryDirectory(prefix="constraint-shift-build-") as cache:
        return _run_harness(languages, output, sources, timeout, output_limit, Path(cache))


def _run_harness(languages: list[str], output: Path, sources: Path,
                 timeout: float, output_limit: int, cache: Path) -> dict:
    if os.name != "posix":
        raise ValueError("Phase 2 currently requires POSIX process groups")
    if not languages or len(languages) != len(set(languages)) or any(l not in ADAPTERS for l in languages):
        raise ValueError("select unique supported languages")
    if (not math.isfinite(timeout) or timeout <= 0 or isinstance(timeout, bool)
            or not isinstance(output_limit, int) or isinstance(output_limit, bool) or output_limit < 1):
        raise ValueError("resource limits must be positive and finite")
    output = output.resolve()
    output.relative_to(ROOT)  # Evidence paths are repository-relative.
    cases = load_cases(TASK / "cases.json")
    tools = {language: resolve_tool(language) for language in languages}
    output.mkdir(parents=True, exist_ok=False)
    common = output / "contract"
    common.mkdir()
    for name, path in {"TASK.md": TASK / "TASK.md", "cases.json": TASK / "cases.json",
                       "harness.py": Path(__file__),
                       "validate_phase1.py": ROOT / "scripts/validate_phase1.py",
                       "schema.json": ROOT / "schema/harness-smoke.schema.json"}.items():
        shutil.copyfile(path, common / name)
    # Read the snapshot used for these trials, not mutable live input files.
    cases = load_cases(common / "cases.json")
    record_validator, schema = retained_record_contract(common)
    source_errors = {}
    source_snapshots = {}
    execution_sources = {}
    # Freeze all selected sources before any compiler, version probe, or candidate runs.
    for language in languages:
        directory = output / language
        directory.mkdir()
        try:
            snapshot = directory / ADAPTERS[language][1]
            shutil.copyfile(sources / language / ADAPTERS[language][1], snapshot)
            source_snapshots[language] = evidence_entry(snapshot, "source", "input")
            work = cache / language / "work"
            work.mkdir(parents=True)
            execution_sources[language] = work / snapshot.name
            shutil.copyfile(snapshot, execution_sources[language])
        except OSError as exc:
            source_errors[language] = str(exc)
    predeclared = {
        "experimental_unit": "one reference task-language smoke execution",
        "acceptance_criteria": ["build exits zero without stdout/stderr diagnostics", "all frozen cases match exact stdout, empty stderr, and exit zero"],
        "resource_limits": [f"{timeout} seconds per process", f"{output_limit} retained stdout+stderr bytes per process"],
        "stopping_rule": "one version probe and build; stop cases at first failure; no repair or retry",
        "inclusion_rule": "retain every selected language, including unavailable toolchains",
        "exclusion_rule": "exclude none after selection",
        "invalid_trial_rule": "missing source/toolchain, unusable version probe, or process-start error is invalid",
        "timeout_rule": "a version, build, or case deadline terminates its process group and marks timeout",
        "missing_data_rule": "unexecuted cases are explicitly listed; unavailable versions are omitted",
        "primary_denominators": ["all selected task-language pairs", "all frozen acceptance cases"],
    }
    plan = {"harness_version": VERSION, "task_id": "TASK-FOLD-001", "languages": languages,
            "tools": tools, "predeclared": predeclared,
            "environment": {"os": platform.platform(), "architecture": platform.machine()},
            "execution_environment": {"LANG": "C", "LC_ALL": "C", "TZ": "UTC",
                                      "GOENV": "off", "GOWORK": "off", "GO111MODULE": "off",
                                      "GOTOOLCHAIN": "local", "CGO_ENABLED": "0"}}
    write_json(common / "plan.json", plan)
    common_files = [(common / "TASK.md", "spec", "input"), (common / "cases.json", "acceptance", "test"),
                    (common / "harness.py", "harness", "input"), (common / "schema.json", "schema", "input"),
                    (common / "validate_phase1.py", "record-validator", "input"),
                    (common / "plan.json", "plan", "environment")]
    common_evidence = [evidence_entry(p, eid, kind) for p, eid, kind in common_files]
    summary = {"harness_version": VERSION, "trials": []}
    run_id = uuid.uuid4().hex
    for language in languages:
        started_at, started_ns = now(), time.monotonic_ns()
        directory = output / language
        env = {"PATH": os.environ.get("PATH", os.defpath), **plan["execution_environment"],
               "GOCACHE": str(cache / language / "go-cache"), "GOPATH": str(cache / language / "go-path")}
        if "HOME" in os.environ:
            env["HOME"] = os.environ["HOME"]
        write_json(directory / "environment.json", env)
        tool = tools[language]
        source = directory / ADAPTERS[language][1]
        result = {"language": language, "version": None, "build": None, "cases": [],
                  "cases_not_run": [c["id"] for c in cases]}
        status, reason = "invalid", "toolchain unavailable"
        build_status, test_status = "not_run", "not_run"
        version = None
        version_status = "error"
        build_command = "build not run"
        if language in source_errors:
            result["source_error"] = source_errors[language]
            reason = "source unavailable"
        else:
            if tool is not None:
                probe = execute([tool, *ADAPTERS[language][3]], directory, b"", timeout, output_limit, env)
                result["version"] = save_execution(directory, "version", probe)
                if probe["status"] == "timeout":
                    status, reason = "timeout", "version probe timed out"
                elif probe["status"] == "output_limit":
                    status, reason, version_status = "failure", "version probe exceeded output limit", "fail"
                elif passed(probe) and (probe["stdout"] or probe["stderr"]).strip():
                    version_status = "pass"
                    version = (probe["stdout"] or probe["stderr"]).decode("utf-8", errors="replace").strip()
                    build_argv, run_argv = commands(language, tool, execution_sources[language], directory / "program")
                    build_command = shlex.join(build_argv)
                    build = execute(build_argv, directory, b"", timeout, output_limit, env)
                    result["build"] = save_execution(directory, "build", build)
                    if not passed(build) or build["stdout"] or build["stderr"]:
                        status = failure_status(build)
                        reason = "build did not complete successfully"
                        build_status = verification_failure(build)
                    else:
                        build_status, test_status = "pass", "pass"
                        status, reason = "success", "all frozen acceptance cases passed"
                        for index, case in enumerate(cases):
                            name = f"case-{index:03d}"
                            stdin = case["input"].encode("ascii")
                            expected = case["expected"].encode("ascii")
                            (directory / f"{name}.input.bin").write_bytes(stdin)
                            (directory / f"{name}.expected.bin").write_bytes(expected)
                            actual = execute(run_argv, directory, stdin, timeout, output_limit, env)
                            envelope = save_execution(directory, name, actual)
                            accepted = passed(actual) and actual["stdout"] == expected and actual["stderr"] == b""
                            result["cases"].append({"id": case["id"], "accepted": accepted, **envelope})
                            result["cases_not_run"].remove(case["id"])
                            if not accepted:
                                status = failure_status(actual)
                                reason = f"acceptance case {case['id']} failed"
                                test_status = verification_failure(actual)
                                break
                else:
                    reason = "toolchain version probe unusable"
        result.update({"status": status, "reason": reason})
        write_json(directory / "result.json", result)
        files = [(p, f"trial-{i}", "build" if p.name == "program" else "log")
                 for i, p in enumerate(sorted(directory.iterdir())) if p.is_file() and p != source]
        evidence = list(common_evidence)
        if language in source_snapshots:
            evidence.append(source_snapshots[language])
        evidence += [evidence_entry(p, eid, kind) for p, eid, kind in files]
        result_ref = next(e["evidence_id"] for e in evidence if e["path"].endswith(f"/{language}/result.json"))
        record = {
            "schema_version": "2.0.0", "record_type": "constraint-shift-harness-smoke",
            "record_id": f"phase2-{run_id}-{language}", "created_at": now(), "hypotheses": [],
            "task": {"task_id": "TASK-FOLD-001", "title": "Bounded integer fold",
                     "equivalence_group": "bounded-integer-fold-1.0.0", "specification_ref": "spec", "acceptance_ref": "acceptance"},
            "agent": {"agent_id": "phase2-reference-runner", "kind": "scripted", "name": "Phase 2 reference fixture runner", "version": VERSION},
            "language": {"name": ADAPTERS[language][0]},
            "toolchain": {"compiler_or_runtime": tool or ADAPTERS[language][2],
                          "build_flags": ADAPTERS[language][4],
                          "dependencies": ["toolchain standard library/runtime; no third-party packages"],
                          "analysis_tools": [], "test_command": "language_harness.py: frozen acceptance cases"},
            "environment": plan["environment"], "predeclared": predeclared,
            "trial": {"trial_id": f"{run_id}-{language}", "attempt": 1,
                      "condition": "reference implementation harness smoke",
                      "factors": [{"name": "language", "value": language}],
                      "started_at": started_at, "ended_at": now(), "status": status,
                      "termination_reason": reason,
                      "measurements": [{"name": "wall_clock_ns", "value": time.monotonic_ns() - started_ns, "unit": "nanoseconds"},
                                       {"name": "cases_executed", "value": len(result["cases"]), "unit": "count"}],
                      "notes": ["Infrastructure smoke only: no hypothesis observation, measured generation/repair trial, or ranking; fixture authorship is outside this execution trial."]},
            "interventions": [],
            "verification_outcomes": [
                {"verifier_id": "toolchain-identity", "kind": "other", "status": version_status,
                 "independent_from_generator": False, "command": "version probe; see retained argv", "evidence_refs": [result_ref]},
                {"verifier_id": "build", "kind": "compile", "status": build_status,
                 "independent_from_generator": False, "command": build_command, "evidence_refs": [result_ref]},
                {"verifier_id": "frozen-cases", "kind": "behavioural", "status": test_status,
                 "independent_from_generator": False, "command": "exact stdout, empty stderr, exit zero; see retained argv",
                 "evidence_refs": ["acceptance", result_ref]},
            ], "evidence": evidence,
        }
        if version:
            record["toolchain"]["version"] = version
        errors = record_validator(record, schema)
        if errors:
            raise ValueError("generated record is invalid: " + "; ".join(errors))
        write_json(directory / "record.json", record)
        summary["trials"].append({"language": language, "status": status,
                                  "record": f"{language}/record.json"})
        write_json(output / "summary.json", summary)
    return summary


def verify_bundle(output: Path) -> list[str]:
    errors = []
    output = output.resolve()
    output.relative_to(ROOT)
    record_validator, schema = retained_record_contract(output / "contract")
    load_cases(output / "contract/cases.json")
    plan = load_json(output / "contract/plan.json")
    summary = load_json(output / "summary.json")
    languages = plan["languages"]
    if (not isinstance(languages, list) or not languages
            or any(not isinstance(language, str) or language not in ADAPTERS for language in languages)
            or len(languages) != len(set(languages))):
        raise ValueError("bundle plan must select nonempty unique supported languages")
    if [t["language"] for t in summary["trials"]] != languages:
        errors.append("summary does not retain every selected language in order")
    for language in languages:
        if language not in ADAPTERS:
            raise ValueError("unknown language in bundle")
        record = load_json(output / language / "record.json")
        record_errors = record_validator(record, schema)
        errors.extend(f"{language}: {e}" for e in record_errors)
        if record_errors:
            continue
        if record["language"]["name"] != ADAPTERS[language][0] or {"name": "language", "value": language} not in record["trial"]["factors"]:
            errors.append(f"{language}: record adapter identity disagrees with directory")
        result_path = output / language / "result.json"
        result = load_json(result_path)
        if (result.get("language") != language or result.get("status") != record["trial"]["status"]
                or result.get("reason") != record["trial"]["termination_reason"]):
            errors.append(f"{language}: record outcome disagrees with retained execution result")
        verification_statuses = {v["verifier_id"]: v["status"] for v in record["verification_outcomes"]}
        if verification_statuses != retained_verification_statuses(output / language, result):
            errors.append(f"{language}: verification outcomes disagree with retained execution result")
        bound_paths = {(ROOT / e["path"]).resolve() for e in record["evidence"]}
        required_paths = [result_path, *(output / "contract" / name for name in
                          ("TASK.md", "cases.json", "harness.py", "schema.json", "validate_phase1.py", "plan.json"))]
        if any(p.resolve() not in bound_paths for p in required_paths):
            errors.append(f"{language}: record does not bind required execution/contract evidence")
        expected = {"language": language, "status": record["trial"]["status"],
                    "record": f"{language}/record.json"}
        if expected not in summary["trials"]:
            errors.append(f"{language}: summary disagrees with retained record")
        for evidence in record.get("evidence", []):
            path = (ROOT / evidence["path"]).resolve()
            if not path.is_relative_to(output):
                errors.append(f"{language}: evidence escapes bundle")
                continue
            try:
                actual = evidence_entry(path, evidence["evidence_id"], evidence["kind"])
            except OSError as exc:
                errors.append(f"{language}: missing evidence: {exc}")
                continue
            if actual["sha256"] != evidence["sha256"] or actual["bytes"] != evidence["bytes"]:
                errors.append(f"{language}: evidence digest/size mismatch: {evidence['path']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list implemented adapters")
    run = sub.add_parser("run", help="execute and retain each selected language")
    run.add_argument("--languages", nargs="+", choices=ADAPTERS, default=list(ADAPTERS))
    run.add_argument("--sources", type=Path, default=SOURCES)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--timeout", type=float, default=30.0)
    run.add_argument("--output-limit", type=int, default=1048576)
    verify = sub.add_parser("verify", help="check records and physical evidence digests")
    verify.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "list":
            for language, adapter in ADAPTERS.items():
                print(f"{language}: {adapter[0]} ({resolve_tool(language) or 'unavailable'})")
            return 0
        if args.command == "verify":
            errors = verify_bundle(args.output)
            for error in errors:
                print(error, file=sys.stderr)
            return int(bool(errors))
        summary = run_harness(args.languages, args.output, args.sources.resolve(), args.timeout, args.output_limit)
        for trial in summary["trials"]:
            print(f"{trial['language']}: {trial['status']}")
        return int(any(t["status"] != "success" for t in summary["trials"]))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
