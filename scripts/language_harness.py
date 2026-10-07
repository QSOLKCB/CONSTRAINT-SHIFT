#!/usr/bin/env python3
"""Phase 2: equivalent-task execution and retained schema 2.0.0 evidence."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from decimal import Decimal
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

from validate_phase1 import load_json, _no_duplicate_keys, _decimal_number

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "harness/tasks/bounded-integer-fold"
SOURCES = ROOT / "harness/implementations"
VERSION = "1.1.0"
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
    tool = sys.executable if language == "python" else shutil.which(ADAPTERS[language][2])
    # PATH components are relative to the caller, not the trial working directory.
    return os.path.abspath(tool) if tool else None


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
    approved = TRUSTED_RECORD_CONTRACTS.get(schema.get("$id")) if isinstance(schema, dict) else None
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


def version_identity(execution: dict) -> str:
    """Select the first nonempty stripped stream, preserving both raw streams."""
    for stream in ("stdout", "stderr"):
        value = execution[stream].strip()
        if value:
            return value.decode("utf-8", errors="replace")
    return ""


def version_accepted(execution: dict) -> bool:
    return passed(execution) and bool(version_identity(execution))


def build_accepted(execution: dict) -> bool:
    return passed(execution) and not execution["stdout"] and not execution["stderr"]


def case_accepted(execution: dict, expected: bytes) -> bool:
    return passed(execution) and execution["stdout"] == expected and execution["stderr"] == b""


def derive_trial(result: dict, observations: dict, frozen_cases: list[dict], tool: str | None) -> tuple:
    """One procedure for producing and checking stage progression and outcomes.

    Observations contain execution envelopes plus captured raw bytes. Conclusions
    (including accepted flags) are checked, never used as acceptance evidence.
    """
    statuses = {"toolchain-identity": "error", "build": "not_run", "frozen-cases": "not_run"}
    version, build, executed = result["version"], result["build"], result["cases"]

    def stopped_before_build():
        if build is not None or executed:
            raise ValueError("build/cases executed after an unavailable or unusable version probe")

    if "source_error" in result or tool is None:
        if version is not None:
            raise ValueError("version probe executed despite missing source/toolchain")
        stopped_before_build()
        reason = "source unavailable" if "source_error" in result else "toolchain unavailable"
        return "invalid", reason, statuses
    if version is None:
        raise ValueError("available source/toolchain requires a version probe")
    probe = observations["version"]
    if not version_accepted(probe):
        stopped_before_build()
        if probe["status"] == "timeout":
            return "timeout", "version probe timed out", statuses
        if probe["status"] == "output_limit":
            statuses["toolchain-identity"] = "fail"
            return "failure", "version probe exceeded output limit", statuses
        return "invalid", "toolchain version probe unusable", statuses
    statuses["toolchain-identity"] = "pass"
    if build is None:
        raise ValueError("usable version probe requires a build result")
    built = observations["build"]
    if not build_accepted(built):
        if executed:
            raise ValueError("cases executed after a rejected build")
        statuses["build"] = verification_failure(built)
        return failure_status(built), "build did not complete successfully", statuses
    statuses["build"] = "pass"
    if not executed:
        raise ValueError("accepted build requires frozen case execution")
    for index, case in enumerate(executed):
        actual = observations[f"case-{index:03d}"]
        accepted = case_accepted(actual, frozen_cases[index]["expected"].encode("ascii"))
        if accepted != case["accepted"]:
            raise ValueError(f"case {case['id']} accepted flag disagrees with raw execution evidence")
        if not accepted:
            if index != len(executed) - 1:
                raise ValueError("cases executed after the first rejected case")
            statuses["frozen-cases"] = verification_failure(actual)
            return failure_status(actual), f"acceptance case {case['id']} failed", statuses
    if len(executed) != len(frozen_cases) or result["cases_not_run"]:
        raise ValueError("accepted execution omits frozen cases")
    statuses["frozen-cases"] = "pass"
    return "success", "all frozen acceptance cases passed", statuses


def integer(value: object) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or (
        isinstance(value, Decimal) and value.is_finite() and value == value.to_integral_value())


def validate_execution(envelope: object, name: str) -> None:
    required = {"argv", "status", "returncode", "elapsed_ns", "stdout_file", "stderr_file"}
    if not isinstance(envelope, dict) or not required <= envelope.keys() or envelope.keys() - required - {"error"}:
        raise ValueError(f"{name}: invalid execution envelope")
    argv = envelope["argv"]
    if (not isinstance(argv, list) or not argv
            or any(not isinstance(a, str) or "\0" in a for a in argv)
            or not Path(argv[0]).is_absolute()):
        raise ValueError(f"{name}: invalid retained argv")
    status, code, elapsed = envelope["status"], envelope["returncode"], envelope["elapsed_ns"]
    if not isinstance(status, str) or status not in ("completed", "timeout", "error", "output_limit"):
        raise ValueError(f"{name}: invalid execution status")
    if (code is not None and not integer(code)) or (status == "completed" and code is None):
        raise ValueError(f"{name}: invalid execution returncode")
    if not integer(elapsed) or elapsed < 0:
        raise ValueError(f"{name}: invalid execution elapsed_ns")
    if "error" in envelope and not isinstance(envelope["error"], str):
        raise ValueError(f"{name}: invalid execution error")
    for stream in ("stdout", "stderr"):
        if envelope[f"{stream}_file"] != f"{name}.{stream}.bin":
            raise ValueError(f"{name}: " + ("retained case coverage: " if name.startswith("case-") else "")
                             + "invalid retained stream filename")


def execution_stages(result: dict):
    for name in ("version", "build"):
        if result[name] is not None:
            yield name, result[name]
    for index, case in enumerate(result["cases"]):
        yield f"case-{index:03d}", {k: v for k, v in case.items() if k not in ("id", "accepted")}


def validate_result(result: object) -> None:
    required = {"language", "status", "reason", "version", "build", "cases", "cases_not_run"}
    if not isinstance(result, dict) or not required <= result.keys() or result.keys() - required - {"source_error"}:
        raise ValueError("invalid retained result object")
    if not isinstance(result["language"], str):
        raise ValueError("invalid result language")
    if not isinstance(result["status"], str) or result["status"] not in ("success", "failure", "timeout", "invalid"):
        raise ValueError("invalid trial status")
    if not isinstance(result["reason"], str) or not result["reason"]:
        raise ValueError("invalid trial reason")
    if "source_error" in result and (not isinstance(result["source_error"], str) or not result["source_error"]):
        raise ValueError("invalid source_error")
    if (not isinstance(result["cases"], list) or not isinstance(result["cases_not_run"], list)
            or any(not isinstance(item, str) for item in result["cases_not_run"])):
        raise ValueError("invalid retained case lists")
    for case in result["cases"]:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or type(case.get("accepted")) is not bool:
            raise ValueError("invalid retained case object")
    for name, envelope in execution_stages(result):
        validate_execution(envelope, name)


def decode_json(data: bytes):
    return json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
                      parse_float=_decimal_number, parse_constant=reject_constant)


def reject_constant(value: str):
    raise ValueError(f"non-JSON numeric constant: {value}")


def retained_case_coverage(result: dict, frozen_cases: list[dict]) -> bool:
    executed = result.get("cases")
    if not isinstance(executed, list) or len(executed) > len(frozen_cases):
        return False
    count = len(executed)
    if (any(not isinstance(case, dict) or type(case.get("accepted")) is not bool for case in executed)
            or [case.get("id") for case in executed] != [case["id"] for case in frozen_cases[:count]]
            or result.get("cases_not_run") != [case["id"] for case in frozen_cases[count:]]
            or any(not case["accepted"] for case in executed[:-1])
            or (0 < count < len(frozen_cases) and executed[-1]["accepted"])):
        return False
    all_passed = count == len(frozen_cases) and all(case["accepted"] for case in executed)
    if (result.get("status") == "success") != all_passed:
        return False
    for index, case in enumerate(executed):
        if any(case.get(f"{stream}_file") != f"case-{index:03d}.{stream}.bin" for stream in ("stdout", "stderr")):
            return False
    return True


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
    with tempfile.TemporaryDirectory(prefix="constraint-shift-build-") as cache, ExitStack() as cleanup:
        return _run_harness(languages, output, sources, timeout, output_limit, Path(cache), cleanup)


def _run_harness(languages: list[str], output: Path, sources: Path,
                 timeout: float, output_limit: int, cache: Path, cleanup: ExitStack) -> dict:
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
    # Executables use the operator-selected output filesystem, not system /tmp.
    execution_root = Path(cleanup.enter_context(tempfile.TemporaryDirectory(
        prefix="execution-", dir=output)))
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
    source_bytes = {}
    # Freeze all selected sources before any compiler, version probe, or candidate runs.
    for language in languages:
        directory = output / language
        directory.mkdir()
        try:
            snapshot = directory / ADAPTERS[language][1]
            shutil.copyfile(sources / language / ADAPTERS[language][1], snapshot)
            source_snapshots[language] = evidence_entry(snapshot, "source", "input")
            source_bytes[language] = snapshot.read_bytes()
            work = execution_root / language / "build"
            work.mkdir(parents=True)
            execution_sources[language] = work / snapshot.name
            execution_sources[language].write_bytes(source_bytes[language])
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
        work = execution_root / language / "build"
        result = {"language": language, "version": None, "build": None, "cases": [],
                  "cases_not_run": [c["id"] for c in cases]}
        observations = {}
        version = None
        artifact_snapshot = None
        artifact_bytes, artifact_mode = None, None
        build_command = "build not run"
        if language in source_errors:
            result["source_error"] = source_errors[language]
        else:
            if tool is not None:
                probe = execute([tool, *ADAPTERS[language][3]], work, b"", timeout, output_limit, env)
                result["version"] = save_execution(directory, "version", probe)
                observations["version"] = probe
                if version_accepted(probe):
                    version = version_identity(probe)
                    work = execution_sources[language].parent
                    build_argv, run_argv = commands(language, tool, execution_sources[language], work / "compiled-program")
                    build_command = shlex.join(build_argv)
                    build = execute(build_argv, work, b"", timeout, output_limit, env)
                    result["build"] = save_execution(directory, "build", build)
                    if language != "python" and build_accepted(build):
                        try:
                            shutil.copy2(work / "compiled-program", directory / "program")
                            artifact_snapshot = evidence_entry(directory / "program", "compiled-artifact", "build")
                            # Keep the input to later execution copies in the parent,
                            # rather than rereading candidate-accessible snapshot files.
                            artifact_bytes = (directory / "program").read_bytes()
                            artifact_mode = (directory / "program").stat().st_mode & 0o777
                        except OSError as exc:
                            build["status"], build["error"] = "error", f"compiled artifact unavailable: {exc}"
                            result["build"] = save_execution(directory, "build", build)
                    observations["build"] = build
                    if build_accepted(build):
                        for index, case in enumerate(cases):
                            name = f"case-{index:03d}"
                            stdin = case["input"].encode("ascii")
                            expected = case["expected"].encode("ascii")
                            (directory / f"{name}.input.bin").write_bytes(stdin)
                            (directory / f"{name}.expected.bin").write_bytes(expected)
                            try:
                                case_work = execution_root / language / name
                                executable = case_work / "execution-program"
                                case_source = case_work / ADAPTERS[language][1]
                                run_argv = ([str(executable)] if artifact_snapshot is not None else
                                            [tool, *ADAPTERS[language][4], str(case_source)])
                                case_work.mkdir()
                                if artifact_snapshot is not None:
                                    # Never overwrite an executable a killed descendant
                                    # might still have mapped: every case gets a new path.
                                    executable.write_bytes(artifact_bytes)
                                    executable.chmod(artifact_mode)
                                else:
                                    # Restore the original Python bytes for every case;
                                    # a candidate may modify only its disposable copy.
                                    case_source.write_bytes(source_bytes[language])
                                actual = execute(run_argv, case_work, stdin, timeout, output_limit, env)
                            except OSError as exc:
                                actual = {"argv": run_argv, "status": "error", "returncode": None,
                                          "stdout": b"", "stderr": b"", "elapsed_ns": 0,
                                          "error": f"execution copy unavailable: {exc}"}
                            envelope = save_execution(directory, name, actual)
                            observations[name] = actual
                            accepted = case_accepted(actual, expected)
                            result["cases"].append({"id": case["id"], "accepted": accepted, **envelope})
                            result["cases_not_run"].remove(case["id"])
                            if not accepted:
                                break
        status, reason, verification_statuses = derive_trial(result, observations, cases, tool)
        result.update({"status": status, "reason": reason})
        write_json(directory / "result.json", result)
        files = [(p, f"trial-{i}", "build" if p.name == "program" else "log")
                 for i, p in enumerate(sorted(directory.iterdir()))
                 if p.is_file() and p != source and (p.name != "program" or artifact_snapshot is None)]
        evidence = list(common_evidence)
        if language in source_snapshots:
            evidence.append(source_snapshots[language])
        if artifact_snapshot is not None:
            evidence.append(artifact_snapshot)
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
                {"verifier_id": "toolchain-identity", "kind": "other", "status": verification_statuses["toolchain-identity"],
                 "independent_from_generator": False, "command": "version probe; see retained argv", "evidence_refs": [result_ref]},
                {"verifier_id": "build", "kind": "compile", "status": verification_statuses["build"],
                 "independent_from_generator": False, "command": build_command, "evidence_refs": [result_ref]},
                {"verifier_id": "frozen-cases", "kind": "behavioural", "status": verification_statuses["frozen-cases"],
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
    frozen_cases = load_cases(output / "contract/cases.json")
    plan = load_json(output / "contract/plan.json")
    if not isinstance(plan, dict):
        return ["invalid bundle plan object"]
    languages = plan.get("languages")
    if (not isinstance(languages, list) or not languages
            or any(not isinstance(language, str) or language not in ADAPTERS for language in languages)
            or len(languages) != len(set(languages))):
        raise ValueError("bundle plan must select nonempty unique supported languages")
    tools = plan.get("tools")
    if (not isinstance(tools, dict) or set(tools) != set(languages)
            or any(tool is not None and (not isinstance(tool, str) or not Path(tool).is_absolute() or "\0" in tool)
                   for tool in tools.values())):
        return ["invalid bundle plan tool selection"]
    if plan.get("harness_version") not in ("1.0.0", VERSION):
        return ["unsupported retained harness procedure version"]
    summary = load_json(output / "summary.json")
    if (not isinstance(summary, dict) or not isinstance(summary.get("trials"), list)
            or summary.get("harness_version") != plan["harness_version"]
            or any(not isinstance(t, dict) or set(t) != {"language", "status", "record"}
                   or any(not isinstance(t[k], str) for k in t)
                   for t in summary["trials"])):
        return ["invalid bundle summary object/trials"]
    if [t["language"] for t in summary["trials"]] != languages:
        errors.append("summary does not retain every selected language in order")
    for language in languages:
        directory = output / language
        try:
            record = load_json(directory / "record.json")
        except (OSError, ValueError) as exc:
            errors.append(f"{language}: invalid retained record: {exc}")
            continue
        record_errors = record_validator(record, schema)
        errors.extend(f"{language}: {e}" for e in record_errors)
        if record_errors:
            continue
        if record["language"]["name"] != ADAPTERS[language][0] or {"name": "language", "value": language} not in record["trial"]["factors"]:
            errors.append(f"{language}: record adapter identity disagrees with directory")
        result_path = directory / "result.json"
        try:
            result = load_json(result_path)
            validate_result(result)
        except (OSError, ValueError) as exc:
            errors.append(f"{language}: invalid retained result: {exc}")
            continue
        if not retained_case_coverage(result, frozen_cases):
            errors.append(f"{language}: retained case coverage disagrees with frozen suite or stopping rule")
            continue
        if (result["language"] != language or result["status"] != record["trial"]["status"]
                or result["reason"] != record["trial"]["termination_reason"]):
            errors.append(f"{language}: record outcome disagrees with retained execution result")
        verifiers = record["verification_outcomes"]
        expected_ids = {"toolchain-identity", "build", "frozen-cases"}
        if len(verifiers) != len(expected_ids) or {v["verifier_id"] for v in verifiers} != expected_ids:
            errors.append(f"{language}: verification outcomes require exactly one of each harness verifier ID")
        verification_statuses = {v["verifier_id"]: v["status"] for v in verifiers}
        expected = {"language": language, "status": record["trial"]["status"],
                    "record": f"{language}/record.json"}
        if expected not in summary["trials"]:
            errors.append(f"{language}: summary disagrees with retained record")

        # Bind and check every physical artifact before using it to infer outcomes.
        required_paths = [result_path, directory / "environment.json", *(output / "contract" / name for name in
                          ("TASK.md", "cases.json", "harness.py", "schema.json", "validate_phase1.py", "plan.json"))]
        required_paths += [directory / f"{name}.{suffix}" for name, _ in execution_stages(result)
                           for suffix in ("json", "stdout.bin", "stderr.bin")]
        required_paths += [directory / f"case-{index:03d}.{suffix}" for index in range(len(result["cases"]))
                           for suffix in ("input.bin", "expected.bin")]
        if "source_error" not in result:
            required_paths.append(directory / ADAPTERS[language][1])
        verified = {}
        integrity_errors = []
        for evidence in record["evidence"]:
            path = (ROOT / evidence["path"]).resolve()
            if not path.is_relative_to(output):
                integrity_errors.append(f"{language}: evidence escapes bundle")
                continue
            if "bytes" not in evidence:
                integrity_errors.append(f"{language}: missing evidence byte count: {evidence['path']}")
                continue
            if path in verified:
                integrity_errors.append(f"{language}: duplicate evidence path: {evidence['path']}")
                continue
            try:
                contents = path.read_bytes()
            except OSError as exc:
                integrity_errors.append(f"{language}: missing evidence: {exc}")
                continue
            if hashlib.sha256(contents).hexdigest() != evidence["sha256"] or len(contents) != evidence["bytes"]:
                integrity_errors.append(f"{language}: evidence digest/size mismatch: {evidence['path']}")
                continue
            verified[path] = contents
        if any(p.resolve() not in verified for p in required_paths):
            integrity_errors.append(f"{language}: record does not bind required execution/contract evidence")
        errors.extend(integrity_errors)
        if integrity_errors:
            continue
        try:
            # Decode exactly the checked bytes; never run candidates during verification.
            checked_result = decode_json(verified[result_path.resolve()])
            if checked_result != result or decode_json(verified[(output / "contract/plan.json").resolve()]) != plan:
                raise ValueError("retained result/plan changed during verification")
            environment = decode_json(verified[(directory / "environment.json").resolve()])
            if not isinstance(environment, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                                       for k, v in environment.items()):
                raise ValueError("invalid retained execution environment")
            observations = {}
            for name, envelope in execution_stages(result):
                physical = decode_json(verified[(directory / f"{name}.json").resolve()])
                validate_execution(physical, name)
                if physical != envelope:
                    raise ValueError(f"{name}: physical execution envelope disagrees with aggregate result")
                observations[name] = {**physical, **{stream: verified[(directory / physical[f"{stream}_file"]).resolve()]
                                                   for stream in ("stdout", "stderr")}}
            for index, case in enumerate(result["cases"]):
                for suffix, field in (("input", "input"), ("expected", "expected")):
                    actual = verified[(directory / f"case-{index:03d}.{suffix}.bin").resolve()]
                    if actual != frozen_cases[index][field].encode("ascii"):
                        raise ValueError(f"case {case['id']}: retained {suffix} differs from frozen suite")
            if language != "python" and "build" in observations and build_accepted(observations["build"]):
                if (directory / "program").resolve() not in verified:
                    raise ValueError("record does not bind required execution/contract evidence: compiled artifact")
            status, reason, derived_verifiers = derive_trial(result, observations, frozen_cases, tools[language])
            if result["status"] != status or result["reason"] != reason:
                raise ValueError("retained outcome disagrees with derived stage outcome")
            if verification_statuses != derived_verifiers:
                raise ValueError("verification outcomes disagree with retained execution result")
            identity = version_identity(observations["version"]) if derived_verifiers["toolchain-identity"] == "pass" else None
            if record["toolchain"].get("version") != identity:
                raise ValueError("record toolchain version disagrees with retained version streams")
        except ValueError as exc:
            errors.append(f"{language}: {exc}")
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
