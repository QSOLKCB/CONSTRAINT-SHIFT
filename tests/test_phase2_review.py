"""Regression gates supplied with the a8167c5 review; retained as repair controls."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get("CONSTRAINT_SHIFT_REVIEW_ROOT",
                          str(Path(__file__).resolve().parents[1]))).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
import language_harness as harness


@unittest.skipUnless(os.name == "posix", "Harness requires POSIX")
class ReviewMergeGates(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="review-gate-", dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.output = self.base / "evidence"

    def reference(self):
        summary = harness.run_harness(["python"], self.output)
        self.assertEqual("success", summary["trials"][0]["status"])
        self.assertEqual([], harness.verify_bundle(self.output))

    def refresh(self, *paths):
        record = harness.load_json(self.output / "python/record.json")
        for entry in record["evidence"]:
            path = ROOT / entry["path"]
            if path in paths:
                entry.update(harness.evidence_entry(path, entry["evidence_id"], entry["kind"]))
        harness.write_json(self.output / "python/record.json", record)
        return record

    def test_control_unmodified_reference_verifies(self):
        self.reference()

    def test_F1_each_python_case_uses_the_frozen_implementation(self):
        sources = self.base / "sources"
        (sources / "python").mkdir(parents=True)
        reference = (harness.SOURCES / "python/main.py").read_text()
        initial = ("from pathlib import Path\nimport sys\n"
                   "tokens = sys.stdin.buffer.read().split()\n"
                   "print('0 0 0' if int(tokens[0]) == 0 else 'wrong')\n"
                   "Path(__file__).write_text(" + repr(reference) + ")\n")
        (sources / "python/main.py").write_text(initial)
        summary = harness.run_harness(["python"], self.output, sources)
        self.assertEqual("failure", summary["trials"][0]["status"])
        self.assertEqual(initial, (self.output / "python/main.py").read_text())
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_F2_case_envelope_must_agree_with_aggregate(self):
        self.reference()
        path = self.output / "python/case-000.json"
        envelope = harness.load_json(path)
        envelope["returncode"] = 23
        harness.write_json(path, envelope)
        self.refresh(path)
        self.assertTrue(harness.verify_bundle(self.output))

    def test_F2_accepted_case_must_agree_with_raw_output(self):
        self.reference()
        path = self.output / "python/case-000.stdout.bin"
        path.write_bytes(b"wrong\n")
        self.refresh(path)
        self.assertTrue(harness.verify_bundle(self.output))

    def test_F3_success_requires_a_successful_build(self):
        self.reference()
        path = self.output / "python/result.json"
        result = harness.load_json(path)
        result["build"]["returncode"] = 17
        harness.write_json(path, result)
        build_path = self.output / "python/build.json"
        harness.write_json(build_path, result["build"])
        record = self.refresh(path, build_path)
        record["verification_outcomes"][1]["status"] = "fail"
        harness.write_json(self.output / "python/record.json", record)
        self.assertTrue(harness.verify_bundle(self.output))

    def test_F4_all_executed_stage_evidence_must_be_bound(self):
        self.reference()
        record = harness.load_json(self.output / "python/record.json")
        record["evidence"] = [entry for entry in record["evidence"]
                              if not Path(entry["path"]).name.startswith(("version.", "build."))
                              and Path(entry["path"]).name != "environment.json"]
        for name in ("version.json", "build.json", "environment.json"):
            (self.output / "python" / name).unlink()
        harness.write_json(self.output / "python/record.json", record)
        self.assertTrue(harness.verify_bundle(self.output))

    def test_F5_generated_mixed_stream_version_bundle_verifies(self):
        tool = self.base / "version-wrapper"
        tool.write_text(f"#!{sys.executable}\nimport sys\n"
                        "sys.stdout.write(' \\n')\nsys.stderr.write('wrapper version 1.0\\n')\n")
        tool.chmod(0o755)
        with patch.object(harness, "resolve_tool", return_value=str(tool)):
            harness.run_harness(["python"], self.output)
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_F6_malformed_result_has_a_controlled_cli_diagnostic(self):
        self.reference()
        path = self.output / "python/result.json"
        harness.write_json(path, [])
        self.refresh(path)
        cli = subprocess.run([sys.executable, str(ROOT / "scripts/language_harness.py"),
                              "verify", str(self.output)], capture_output=True, timeout=10)
        self.assertIn(cli.returncode, (1, 2))
        self.assertNotIn(b"Traceback", cli.stderr)
        self.assertTrue(cli.stderr.strip())

    def relabel(self, status, reason=None):
        result_path = self.output / "python/result.json"
        result = harness.load_json(result_path)
        result["status"] = status
        if reason is not None:
            result["reason"] = reason
        harness.write_json(result_path, result)
        record = self.refresh(result_path)
        record["trial"].update(status=status, termination_reason=result["reason"])
        harness.write_json(self.output / "python/record.json", record)
        summary = harness.load_json(self.output / "summary.json")
        summary["trials"][0]["status"] = status
        harness.write_json(self.output / "summary.json", summary)

    def test_failure_cannot_be_relabelled_timeout_or_invalid(self):
        sources = self.base / "sources"
        (sources / "python").mkdir(parents=True)
        (sources / "python/main.py").write_text("print('wrong')\n")
        harness.run_harness(["python"], self.output, sources)
        for status in ("timeout", "invalid"):
            with self.subTest(status=status):
                self.relabel(status)
                self.assertTrue(any("derived stage outcome" in e for e in harness.verify_bundle(self.output)))

    def test_accepted_flags_are_checked_in_both_directions(self):
        self.reference()
        result_path = self.output / "python/result.json"
        result = harness.load_json(result_path)
        result["cases"][-1]["accepted"] = False
        harness.write_json(result_path, result)
        self.refresh(result_path)
        self.relabel("failure", "acceptance case " + result["cases"][-1]["id"] + " failed")
        self.assertTrue(any("accepted flag" in e for e in harness.verify_bundle(self.output)))

    def test_duplicate_verifier_ids_cannot_be_collapsed(self):
        self.reference()
        for status in ("fail", "pass"):
            with self.subTest(status=status):
                record = harness.load_json(self.output / "python/record.json")
                record["verification_outcomes"] = record["verification_outcomes"][-3:]
                duplicate = dict(record["verification_outcomes"][-1], status=status)
                record["verification_outcomes"].insert(0, duplicate)
                harness.write_json(self.output / "python/record.json", record)
                self.assertTrue(any("exactly one" in e for e in harness.verify_bundle(self.output)))

    def test_optional_schema_byte_count_is_required_by_bundle_verifier(self):
        self.reference()
        record = harness.load_json(self.output / "python/record.json")
        del record["evidence"][0]["bytes"]
        harness.write_json(self.output / "python/record.json", record)
        self.assertTrue(any("missing evidence byte count" in e for e in harness.verify_bundle(self.output)))
        cli = subprocess.run([sys.executable, str(ROOT / "scripts/language_harness.py"),
                              "verify", str(self.output)], capture_output=True, timeout=10)
        self.assertEqual(1, cli.returncode)
        self.assertNotIn(b"Traceback", cli.stderr)

    def test_inputs_and_expected_bytes_must_match_the_frozen_suite(self):
        self.reference()
        for suffix in ("input", "expected"):
            with self.subTest(suffix=suffix):
                path = self.output / f"python/case-000.{suffix}.bin"
                original = path.read_bytes()
                path.write_bytes(b"1 1\n")
                self.refresh(path)
                self.assertTrue(any("differs from frozen suite" in e for e in harness.verify_bundle(self.output)))
                path.write_bytes(original)
                self.refresh(path)

    def test_every_stage_envelope_must_match_aggregate_fields(self):
        self.reference()
        for stage in ("version", "build", "case-000"):
            for field, value in (("returncode", 7), ("status", "timeout"), ("elapsed_ns", 0),
                                 ("argv", ["/different/executable"])):
                with self.subTest(stage=stage, field=field):
                    path = self.output / f"python/{stage}.json"
                    original = harness.load_json(path)
                    harness.write_json(path, dict(original, **{field: value}))
                    self.refresh(path)
                    self.assertTrue(any("physical execution envelope disagrees" in e for e in harness.verify_bundle(self.output)))
                    harness.write_json(path, original)
                    self.refresh(path)

    def test_stage_progression_rejects_missing_or_failed_prerequisites(self):
        self.reference()
        result_path = self.output / "python/result.json"
        original = harness.load_json(result_path)
        for stage in ("version", "build"):
            for missing in (False, True):
                with self.subTest(stage=stage, missing=missing):
                    result = harness.decode_json(result_path.read_bytes())
                    result[stage] = None if missing else dict(original[stage], returncode=9)
                    harness.write_json(result_path, result)
                    paths = [result_path]
                    stage_path = self.output / f"python/{stage}.json"
                    if not missing:
                        harness.write_json(stage_path, result[stage])
                        paths.append(stage_path)
                    self.refresh(*paths)
                    errors = harness.verify_bundle(self.output)
                    self.assertTrue(any("requires a" in e or "cases executed" in e for e in errors), errors)
                    harness.write_json(result_path, original)
                    harness.write_json(stage_path, original[stage])
                    self.refresh(result_path, stage_path)

    def test_build_diagnostics_prevent_cases_even_with_zero_exit(self):
        self.reference()
        path = self.output / "python/build.stderr.bin"
        path.write_bytes(b"warning\n")
        self.refresh(path)
        self.assertTrue(any("cases executed after a rejected build" in e for e in harness.verify_bundle(self.output)))

    def test_each_stage_and_environment_requires_a_manifest_binding(self):
        self.reference()
        record_path = self.output / "python/record.json"
        original = harness.load_json(record_path)
        for name in ("environment.json", "version.json", "version.stdout.bin", "version.stderr.bin",
                     "build.json", "build.stdout.bin", "build.stderr.bin"):
            with self.subTest(name=name):
                record = dict(original, evidence=[e for e in original["evidence"] if Path(e["path"]).name != name])
                harness.write_json(record_path, record)
                self.assertTrue(any("required execution/contract evidence" in e for e in harness.verify_bundle(self.output)))
        harness.write_json(record_path, original)
        with patch.object(harness, "execute", side_effect=AssertionError("verification must not execute")):
            self.assertEqual([], harness.verify_bundle(self.output))

    def test_malformed_result_stage_and_summary_shapes_are_controlled(self):
        self.reference()
        result_path = self.output / "python/result.json"
        original = harness.load_json(result_path)
        for value in (None, [], "result", {}, dict(original, version=[]), dict(original, build="build"),
                      dict(original, cases=[None]), dict(original, cases_not_run=None)):
            with self.subTest(value=value):
                harness.write_json(result_path, value)
                self.refresh(result_path)
                self.assertTrue(harness.verify_bundle(self.output))
                cli = subprocess.run([sys.executable, str(ROOT / "scripts/language_harness.py"),
                                      "verify", str(self.output)], capture_output=True, timeout=10)
                self.assertEqual(1, cli.returncode)
                self.assertNotIn(b"Traceback", cli.stderr)
        harness.write_json(result_path, original)
        self.refresh(result_path)
        for value in (None, [], {}, {"harness_version": harness.VERSION, "trials": [None]}):
            with self.subTest(summary=value):
                harness.write_json(self.output / "summary.json", value)
                self.assertTrue(harness.verify_bundle(self.output))

    def test_python_execution_copy_failure_is_retained_and_verifies(self):
        write_bytes = Path.write_bytes

        def fail_second_copy(path, contents):
            if path.parent.name == "case-001" and path.name == "main.py":
                raise OSError("simulated copy failure")
            return write_bytes(path, contents)

        with patch.object(Path, "write_bytes", new=fail_second_copy):
            summary = harness.run_harness(["python"], self.output)
        self.assertEqual("invalid", summary["trials"][0]["status"])
        result = harness.load_json(self.output / "python/result.json")
        self.assertEqual(2, len(result["cases"]))
        self.assertEqual("error", result["cases"][-1]["status"])
        self.assertEqual("case-001", Path(result["cases"][-1]["argv"][-1]).parent.name)
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_new_procedure_version_preserves_task_and_record_versions(self):
        self.reference()
        record = harness.load_json(self.output / "python/record.json")
        plan = harness.load_json(self.output / "contract/plan.json")
        self.assertEqual("1.1.0", plan["harness_version"])
        self.assertEqual("1.1.0", record["agent"]["version"])
        self.assertEqual("2.0.0", record["schema_version"])
        self.assertEqual("bounded-integer-fold-1.0.0", record["task"]["equivalence_group"])
        cases = harness.load_cases(self.output / "contract/cases.json")
        self.assertEqual(8, len(cases))
        paths = [Path(case["argv"][-1]) for case in harness.load_json(self.output / "python/result.json")["cases"]]
        self.assertEqual(8, len(set(paths)))
        self.assertTrue(all(path.parent.name.startswith("case-") and path.is_relative_to(self.output) for path in paths))
        self.assertFalse(list(self.output.glob("execution-*")))


if __name__ == "__main__":
    unittest.main()
