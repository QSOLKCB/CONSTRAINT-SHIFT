"""Regression gates supplied with the a8167c5 review; retained as repair controls."""
import os
from pathlib import Path
import subprocess
import shutil
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

    def refresh(self, *paths, language="python"):
        record = harness.load_json(self.output / f"{language}/record.json")
        for entry in record["evidence"]:
            path = ROOT / entry["path"]
            if path in paths:
                entry.update(harness.evidence_entry(path, entry["evidence_id"], entry["kind"]))
        harness.write_json(self.output / f"{language}/record.json", record)
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

    def old_python_bundle(self):
        # A consistent 1.0.0 execution layout: syntax check and all cases share
        # the same source path. Keep the candidate, streams, and outcomes intact.
        with patch.object(harness, "VERSION", "1.0.0"):
            harness.run_harness(["python"], self.output)
        result_path = self.output / "python/result.json"
        result = harness.load_json(result_path)
        source = result["build"]["argv"][-1]
        paths = [result_path]
        for index, case in enumerate(result["cases"]):
            case["argv"] = [result["version"]["argv"][0], "-I", "-B", source]
            path = self.output / f"python/case-{index:03d}.json"
            harness.write_json(path, {k: v for k, v in case.items() if k not in ("id", "accepted")})
            paths.append(path)
        harness.write_json(result_path, result)
        self.refresh(*paths)
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_procedure_metadata_cannot_upgrade_a_legacy_execution(self):
        self.old_python_bundle()
        plan_path = self.output / "contract/plan.json"
        plan = harness.load_json(plan_path)
        plan["harness_version"] = "1.1.0"
        harness.write_json(plan_path, plan)
        summary_path = self.output / "summary.json"
        summary = harness.load_json(summary_path)
        summary["harness_version"] = "1.1.0"
        harness.write_json(summary_path, summary)
        record = self.refresh(plan_path)
        self.assertTrue(any("procedure version" in e for e in harness.verify_bundle(self.output)))
        # Matching all version labels still cannot upgrade the old shared paths.
        record["agent"]["version"] = "1.1.0"
        harness.write_json(self.output / "python/record.json", record)
        self.assertTrue(any("argv" in e for e in harness.verify_bundle(self.output)))

    def test_retained_version_argv_must_match_the_selected_tool(self):
        self.reference()
        result_path = self.output / "python/result.json"
        result = harness.load_json(result_path)
        result["version"]["argv"] = ["/bin/false", "--fabricated"]
        harness.write_json(result_path, result)
        version_path = self.output / "python/version.json"
        harness.write_json(version_path, result["version"])
        self.refresh(result_path, version_path)
        self.assertTrue(any("argv" in e for e in harness.verify_bundle(self.output)))

    def test_retained_environment_must_match_frozen_plan_settings(self):
        self.reference()
        path = self.output / "python/environment.json"
        env = harness.load_json(path)
        env["LC_ALL"] = "definitely-not-C"
        harness.write_json(path, env)
        self.refresh(path)
        self.assertTrue(any("environment" in e for e in harness.verify_bundle(self.output)))

    def test_case_count_measurement_must_match_retained_execution(self):
        self.reference()
        path = self.output / "python/record.json"
        record = harness.load_json(path)
        count = next(m for m in record["trial"]["measurements"] if m["name"] == "cases_executed")
        count["value"] = 0
        harness.write_json(path, record)
        self.assertTrue(any("cases_executed" in e for e in harness.verify_bundle(self.output)))

    def change_argv(self, language, stage, argv):
        result_path = self.output / language / "result.json"
        result = harness.load_json(result_path)
        envelope = result[stage] if stage in ("version", "build") else result["cases"][int(stage[5:])]
        envelope["argv"] = argv
        physical = self.output / language / f"{stage}.json"
        harness.write_json(physical, {k: v for k, v in envelope.items() if k not in ("id", "accepted")})
        harness.write_json(result_path, result)
        self.refresh(result_path, physical, language=language)

    def test_all_adapter_commands_reject_changed_flags_tools_and_paths(self):
        tool = self.base / "fake-compiler"
        reference = (harness.SOURCES / "python/main.py").read_text()
        tool.write_text(f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\n"
                        "if '-o' not in sys.argv:\n print('fake tool 1.0')\nelse:\n"
                        " target = Path(sys.argv[sys.argv.index('-o') + 1])\n"
                        " target.write_text(" + repr(f"#!{sys.executable}\n" + reference) + ")\n"
                        " target.chmod(0o755)\n")
        tool.chmod(0o755)
        languages = ["c", "cpp", "rust", "go", "python"]
        with patch.object(harness, "resolve_tool", side_effect=lambda lang: sys.executable if lang == "python" else str(tool)):
            summary = harness.run_harness(languages, self.output)
        self.assertTrue(all(t["status"] == "success" for t in summary["trials"]))
        self.assertEqual([], harness.verify_bundle(self.output))
        for language in languages:
            result = harness.load_json(self.output / language / "result.json")
            mutations = [("version", [result["version"]["argv"][0], "--fabricated"]),
                         ("build", ["/bin/false", *result["build"]["argv"][1:]]),
                         ("build", [*result["build"]["argv"], "--fabricated"]),
                         ("case-000", [*result["cases"][0]["argv"], "--fabricated"]),
                         ("case-001", result["cases"][0]["argv"])]
            for stage, argv in mutations:
                with self.subTest(language=language, stage=stage, argv=argv):
                    original = result[stage]["argv"] if stage in ("version", "build") else result["cases"][int(stage[5:])]["argv"]
                    self.change_argv(language, stage, argv)
                    errors = harness.verify_bundle(self.output)
                    self.assertTrue(any("argv" in e for e in errors), errors)
                    self.change_argv(language, stage, original)
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_python_build_and_case_source_paths_cannot_be_substituted(self):
        self.reference()
        result = harness.load_json(self.output / "python/result.json")
        for argv in (result["build"]["argv"][:-1] + ["/outside/build/main.py"],
                     result["build"]["argv"][:-1] + [result["build"]["argv"][-1].replace("/build/", "/other/")],
                     result["build"]["argv"][:4] + ["print('fabricated')", result["build"]["argv"][-1]]):
            with self.subTest(argv=argv):
                self.change_argv("python", "build", argv)
                self.assertTrue(any("argv" in e for e in harness.verify_bundle(self.output)))
                self.change_argv("python", "build", result["build"]["argv"])
        for source in (result["build"]["argv"][-1], "/outside/case-000/main.py"):
            with self.subTest(source=source):
                self.change_argv("python", "case-000", result["cases"][0]["argv"][:-1] + [source])
                self.assertTrue(any("argv" in e for e in harness.verify_bundle(self.output)))
                self.change_argv("python", "case-000", result["cases"][0]["argv"])

    def test_every_declared_environment_setting_is_required_and_frozen(self):
        self.reference()
        path = self.output / "python/environment.json"
        original = harness.load_json(path)
        plan_path = self.output / "contract/plan.json"
        plan = harness.load_json(plan_path)
        for key in plan["execution_environment"]:
            with self.subTest(key=key):
                changed = dict(original)
                del changed[key]
                harness.write_json(path, changed)
                self.refresh(path)
                self.assertTrue(any("environment" in e for e in harness.verify_bundle(self.output)))
        harness.write_json(path, original)
        self.refresh(path)
        # Matching tampered settings in both files cannot redefine this procedure.
        changed_plan = dict(plan, execution_environment=dict(plan["execution_environment"], LC_ALL="wrong"))
        harness.write_json(plan_path, changed_plan)
        harness.write_json(path, dict(original, LC_ALL="wrong"))
        self.refresh(path, plan_path)
        self.assertTrue(any("frozen procedure settings" in e for e in harness.verify_bundle(self.output)))

    def test_case_count_measurement_is_required_unique_and_uses_count_units(self):
        self.reference()
        path = self.output / "python/record.json"
        original = path.read_bytes()
        for mutation in ("missing", "duplicate", "unit"):
            with self.subTest(mutation=mutation):
                record = harness.decode_json(original)
                measurements = record["trial"]["measurements"]
                count = next(m for m in measurements if m["name"] == "cases_executed")
                if mutation == "missing":
                    measurements.remove(count)
                elif mutation == "duplicate":
                    measurements.append(dict(count, value=count["value"] + 1))
                else:
                    count["unit"] = "seconds"
                harness.write_json(path, record)
                errors = harness.verify_bundle(self.output)
                self.assertTrue(any("cases_executed" in e or "measurement names must be unique" in e
                                    for e in errors), errors)
        path.write_bytes(original)
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_case_count_matches_partial_failure_and_unavailable_trials(self):
        sources = self.base / "sources"
        (sources / "python").mkdir(parents=True)
        (sources / "python/main.py").write_text("print('wrong')\n")
        for available, count in ((True, 1), (False, 0)):
            with self.subTest(available=available):
                self.output = self.base / f"count-{available}"
                with patch.object(harness, "resolve_tool", return_value=sys.executable if available else None):
                    harness.run_harness(["python"], self.output, sources)
                self.assertEqual([], harness.verify_bundle(self.output))
                path = self.output / "python/record.json"
                record = harness.load_json(path)
                measurement = next(m for m in record["trial"]["measurements"] if m["name"] == "cases_executed")
                self.assertEqual(count, measurement["value"])
                measurement["value"] = count + 1
                harness.write_json(path, record)
                self.assertTrue(any("cases_executed" in e for e in harness.verify_bundle(self.output)))

    def test_legacy_python_layouts_remain_valid_without_version_upgrade(self):
        self.old_python_bundle()
        result_path = self.output / "python/result.json"
        original = harness.load_json(result_path)
        for source in (str(self.output / "python/main.py"), "/tmp/constraint-shift-build-legacy/python/work/main.py"):
            with self.subTest(source=source):
                self.change_argv("python", "build", original["build"]["argv"][:-1] + [source])
                for index in range(len(original["cases"])):
                    self.change_argv("python", f"case-{index:03d}", original["cases"][index]["argv"][:-1] + [source])
                self.assertEqual([], harness.verify_bundle(self.output))

    def test_archived_commands_verify_from_another_checkout_root(self):
        self.reference()
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                if legacy:
                    self.output = self.base / "legacy-evidence"
                    self.old_python_bundle()
                moved_root = self.base / f"moved-root-{legacy}"
                moved_output = moved_root / self.output.relative_to(ROOT)
                shutil.copytree(self.output, moved_output)
                with patch.object(harness, "ROOT", moved_root):
                    self.assertEqual([], harness.verify_bundle(moved_output))


if __name__ == "__main__":
    unittest.main()
