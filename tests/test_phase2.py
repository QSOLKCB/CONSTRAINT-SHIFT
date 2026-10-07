from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import language_harness as harness


@unittest.skipUnless(os.name == "posix", "Phase 2 requires POSIX process groups")
class LanguageHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="phase2-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.output = self.base / "evidence"

    def sources(self, code: str) -> Path:
        root = self.base / "candidate sources"
        (root / "python").mkdir(parents=True)
        (root / "python/main.py").write_text(code, encoding="utf-8")
        return root

    def record(self, language="python") -> dict:
        return harness.load_json(self.output / language / "record.json")

    def result(self, language="python") -> dict:
        return harness.load_json(self.output / language / "result.json")

    def fake_tool(self, body: str) -> str:
        path = self.base / "fake-compiler"
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(0o755)
        return str(path)

    def assert_valid_bundle(self):
        self.assertEqual([], harness.verify_bundle(self.output))

    def test_every_available_reference_adapter_passes_same_cases(self):
        languages = [name for name in harness.ADAPTERS if harness.resolve_tool(name)]
        self.assertIn("python", languages)
        summary = harness.run_harness(languages, self.output, timeout=60)
        self.assertEqual(languages, [t["language"] for t in summary["trials"]])
        contracts = set()
        for language in languages:
            with self.subTest(language=language):
                record = self.record(language)
                self.assertEqual("success", record["trial"]["status"])
                self.assertEqual(8, len(self.result(language)["cases"]))
                self.assertEqual([], self.result(language)["cases_not_run"])
                self.assertEqual("scripted", record["agent"]["kind"])
                self.assertEqual("constraint-shift-harness-smoke", record["record_type"])
                self.assertEqual([], record["hypotheses"])
                self.assertTrue(all(not v["independent_from_generator"] for v in record["verification_outcomes"]))
                contracts.add(tuple(e["sha256"] for e in record["evidence"] if e["evidence_id"] in ("spec", "acceptance")))
        self.assertEqual(1, len(contracts))
        self.assert_valid_bundle()

    def test_missing_toolchain_retains_invalid_record_and_not_run_verification(self):
        with patch.object(harness, "resolve_tool", return_value=None):
            summary = harness.run_harness(["rust", "go"], self.output)
        self.assertEqual(["invalid", "invalid"], [t["status"] for t in summary["trials"]])
        for language in ("rust", "go"):
            record = self.record(language)
            self.assertNotIn("version", record["toolchain"])
            self.assertEqual(["error", "not_run", "not_run"], [v["status"] for v in record["verification_outcomes"]])
            self.assertEqual(8, len(self.result(language)["cases_not_run"]))
        self.assert_valid_bundle()

    def test_all_sources_are_frozen_before_the_first_process(self):
        source = self.sources((harness.SOURCES / "python/main.py").read_text())
        (source / "go").mkdir()
        original = (harness.SOURCES / "go/main.go").read_bytes()
        (source / "go/main.go").write_bytes(original)
        execute = harness.execute
        resolve = harness.resolve_tool

        def mutate_live_sources(*args, **kwargs):
            (source / "python/main.py").write_text("print('changed after selection')\n")
            (source / "go/main.go").write_text("changed after selection\n")
            return execute(*args, **kwargs)

        with patch.object(harness, "execute", side_effect=mutate_live_sources), patch.object(
            harness, "resolve_tool", side_effect=lambda name: None if name == "go" else resolve(name)
        ):
            summary = harness.run_harness(["python", "go"], self.output, source)
        self.assertEqual(["success", "invalid"], [t["status"] for t in summary["trials"]])
        self.assertEqual(original, (self.output / "go/main.go").read_bytes())
        self.assert_valid_bundle()

    def test_missing_source_is_retained(self):
        self.sources("print('unused')\n")
        harness.run_harness(["c"], self.output, self.base / "candidate sources")
        self.assertEqual("invalid", self.record("c")["trial"]["status"])
        self.assertIn("source_error", self.result("c"))
        self.assert_valid_bundle()

    def test_compile_failure_preserves_diagnostics_and_continues_other_languages(self):
        tool = self.fake_tool("import sys\nif '--version' in sys.argv:\n print('fake C compiler 1.0')\nelse:\n print('retained compile defect', file=sys.stderr)\n sys.exit(4)\n")
        real = harness.resolve_tool
        with patch.object(harness, "resolve_tool", side_effect=lambda name: tool if name == "c" else real(name)):
            summary = harness.run_harness(["c", "python"], self.output)
        self.assertEqual(["failure", "success"], [t["status"] for t in summary["trials"]])
        self.assertIn(b"retained compile defect", (self.output / "c/build.stderr.bin").read_bytes())
        self.assertEqual("not_run", self.record("c")["verification_outcomes"][2]["status"])
        self.assert_valid_bundle()

    def test_python_syntax_failure_is_compile_failure(self):
        harness.run_harness(["python"], self.output, self.sources("def bad(:\n"))
        self.assertEqual("failure", self.record()["trial"]["status"])
        self.assertEqual("fail", self.record()["verification_outcomes"][1]["status"])
        self.assertEqual([], self.result()["cases"])
        self.assert_valid_bundle()

    def test_wrong_output_stops_at_first_case_and_retains_raw_bytes(self):
        harness.run_harness(["python"], self.output, self.sources("import sys\nsys.stdout.buffer.write(b'wrong\\x00\\xff')\n"))
        self.assertEqual("failure", self.record()["trial"]["status"])
        result = self.result()
        self.assertEqual(1, len(result["cases"]))
        self.assertEqual(7, len(result["cases_not_run"]))
        self.assertEqual(b"wrong\x00\xff", (self.output / "python/case-000.stdout.bin").read_bytes())
        self.assert_valid_bundle()

    def test_nonzero_exit_and_stderr_are_rejected(self):
        for index, code in enumerate(("import sys\nprint('0 0 0')\nsys.exit(7)\n", "import sys\nprint('0 0 0')\nprint('unexpected', file=sys.stderr)\n")):
            with self.subTest(code=code):
                self.output = self.base / f"evidence-{index}"
                root = self.base / f"source-{index}"
                (root / "python").mkdir(parents=True)
                (root / "python/main.py").write_text(code)
                harness.run_harness(["python"], self.output, root)
                self.assertEqual("failure", self.record()["trial"]["status"])
                self.assert_valid_bundle()

    def test_runtime_timeout_is_retained(self):
        harness.run_harness(["python"], self.output, self.sources("import time\ntime.sleep(20)\n"), timeout=0.2)
        self.assertEqual("timeout", self.record()["trial"]["status"])
        self.assertEqual("timeout", self.result()["cases"][0]["status"])
        self.assert_valid_bundle()

    def test_build_timeout_is_retained(self):
        tool = self.fake_tool("import sys, time\nif '--version' in sys.argv:\n print('fake C compiler 1.0')\nelse:\n time.sleep(20)\n")
        with patch.object(harness, "resolve_tool", return_value=tool):
            harness.run_harness(["c"], self.output, timeout=0.2)
        self.assertEqual("timeout", self.record("c")["trial"]["status"])
        self.assertEqual("error", self.record("c")["verification_outcomes"][1]["status"])
        self.assert_valid_bundle()

    def test_output_limit_bounds_capture_and_retains_failure(self):
        code = "import os\nwhile True: os.write(1, b'x' * 8192)\n"
        harness.run_harness(["python"], self.output, self.sources(code), output_limit=1024)
        self.assertEqual("failure", self.record()["trial"]["status"])
        self.assertEqual("output_limit", self.result()["cases"][0]["status"])
        self.assertEqual("fail", self.record()["verification_outcomes"][2]["status"])
        self.assertEqual(1024, (self.output / "python/case-000.stdout.bin").stat().st_size)
        self.assert_valid_bundle()

    def test_descendant_holding_pipes_is_terminated_on_deadline(self):
        marker = self.base / "child-pid"
        code = "import os, time\nif os.fork() == 0:\n open(" + repr(str(marker)) + ", 'w').write(str(os.getpid()))\n time.sleep(20)\n"
        result = harness.execute([sys.executable, "-c", code], self.base, b"", 0.2, 1024, dict(os.environ))
        self.assertEqual("timeout", result["status"])
        self.assertLess(result["elapsed_ns"], 2_000_000_000)
        pid = int(marker.read_text())
        status = Path(f"/proc/{pid}/status")
        deadline = time.monotonic() + 1
        while True:
            try:
                observed = status.read_text()
            except FileNotFoundError:
                break
            if "Z (zombie)" in observed:
                break
            if time.monotonic() >= deadline:
                self.fail(f"descendant did not terminate after group SIGKILL: {observed}")
            time.sleep(0.01)

    def test_unusable_version_probe_is_invalid(self):
        tool = self.fake_tool("import sys\nprint('broken tool', file=sys.stderr)\nsys.exit(3)\n")
        with patch.object(harness, "resolve_tool", return_value=tool):
            harness.run_harness(["python"], self.output)
        self.assertEqual("invalid", self.record()["trial"]["status"])
        self.assert_valid_bundle()

    def test_tampered_and_missing_evidence_are_detected(self):
        harness.run_harness(["python"], self.output)
        path = self.output / "python/case-000.stdout.bin"
        path.write_bytes(b"modified")
        self.assertTrue(any("digest/size mismatch" in e for e in harness.verify_bundle(self.output)))
        path.unlink()
        self.assertTrue(any("missing evidence" in e for e in harness.verify_bundle(self.output)))

    def test_summary_cannot_omit_a_selected_language_or_change_outcome(self):
        harness.run_harness(["python"], self.output)
        path = self.output / "summary.json"
        summary = harness.load_json(path)
        summary["trials"][0]["status"] = "failure"
        harness.write_json(path, summary)
        self.assertTrue(any("summary disagrees" in e for e in harness.verify_bundle(self.output)))
        summary["trials"] = []
        harness.write_json(path, summary)
        self.assertTrue(any("every selected language" in e for e in harness.verify_bundle(self.output)))

    def test_evidence_cannot_escape_bundle(self):
        harness.run_harness(["python"], self.output)
        record = self.record()
        record["evidence"][0]["path"] = "README.md"
        harness.write_json(self.output / "python/record.json", record)
        self.assertTrue(any("escapes bundle" in e for e in harness.verify_bundle(self.output)))

    def test_bad_suite_is_rejected_before_trials(self):
        suite = harness.load_json(harness.TASK / "cases.json")
        suite["cases"][0]["expected"] = "0 1 0\n"
        path = self.base / "bad-cases.json"
        harness.write_json(path, suite)
        with self.assertRaisesRegex(ValueError, "oracle disagrees"):
            harness.load_cases(path)

    def test_frozen_suite_rejects_removed_reordered_renamed_or_changed_cases(self):
        original = harness.load_json(harness.TASK / "cases.json")
        variants = []
        for change in ("remove", "reorder", "rename", "input"):
            suite = json.loads(json.dumps(original))
            if change == "remove":
                suite["cases"].pop()
            elif change == "reorder":
                suite["cases"].reverse()
            elif change == "rename":
                suite["cases"][0]["id"] = "different-empty"
            else:
                suite["cases"][0]["input"] = "0\n"
            variants.append(suite)
        path = self.base / "changed-cases.json"
        for suite in variants:
            with self.subTest(suite=suite):
                harness.write_json(path, suite)
                with self.assertRaisesRegex(ValueError, "frozen suite"):
                    harness.load_cases(path)

    def test_record_and_summary_cannot_contradict_execution_result(self):
        harness.run_harness(["python"], self.output)
        record = self.record()
        record["trial"]["status"] = "failure"
        harness.write_json(self.output / "python/record.json", record)
        summary = harness.load_json(self.output / "summary.json")
        summary["trials"][0]["status"] = "failure"
        harness.write_json(self.output / "summary.json", summary)
        self.assertTrue(any("outcome disagrees" in e for e in harness.verify_bundle(self.output)))

    def test_same_status_records_cannot_be_swapped_between_adapters(self):
        with patch.object(harness, "resolve_tool", return_value=None):
            harness.run_harness(["c", "python"], self.output)
        c = (self.output / "c/record.json").read_bytes()
        python = (self.output / "python/record.json").read_bytes()
        (self.output / "c/record.json").write_bytes(python)
        (self.output / "python/record.json").write_bytes(c)
        self.assertTrue(any("adapter identity" in e for e in harness.verify_bundle(self.output)))

    def test_build_diagnostics_with_zero_exit_are_failures(self):
        tool = self.fake_tool("import sys\nif '--version' in sys.argv:\n print('fake C compiler 1.0')\nelse:\n print('warning', file=sys.stderr)\n")
        with patch.object(harness, "resolve_tool", return_value=tool):
            harness.run_harness(["c"], self.output)
        self.assertEqual(0, self.result("c")["build"]["returncode"])
        self.assertEqual("failure", self.record("c")["trial"]["status"])
        self.assertEqual(["pass", "fail", "not_run"], [v["status"] for v in self.record("c")["verification_outcomes"]])
        self.assert_valid_bundle()

    def test_version_and_build_output_overflow_are_failures(self):
        for stage in ("version", "build"):
            with self.subTest(stage=stage):
                self.output = self.base / f"overflow-{stage}"
                body = "import sys, os\nif '--version' in sys.argv:\n "
                body += "os.write(1, b'x' * 8192)\n" if stage == "version" else "print('fake C compiler 1.0')\n"
                body += "else:\n os.write(1, b'x' * 8192)\n"
                tool = self.fake_tool(body)
                with patch.object(harness, "resolve_tool", return_value=tool):
                    harness.run_harness(["c"], self.output, output_limit=1024)
                self.assertEqual("failure", self.record("c")["trial"]["status"])
                index = 0 if stage == "version" else 1
                self.assertEqual("fail", self.record("c")["verification_outcomes"][index]["status"])
                self.assert_valid_bundle()

    def test_retained_contract_survives_incompatible_current_validator(self):
        harness.run_harness(["python"], self.output)
        import validate_phase1
        with patch.object(validate_phase1, "SUPPORTED_SCHEMA_VERSION", "3.0.0"), patch.object(
            validate_phase1, "validate_record", side_effect=RuntimeError("current contract differs")
        ):
            self.assert_valid_bundle()

    def test_unknown_snapshot_code_and_schema_are_rejected_without_execution(self):
        harness.run_harness(["python"], self.output)
        path = self.output / "contract/validate_phase1.py"
        marker = self.base / "must-not-execute"
        original = path.read_bytes()
        path.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('executed')\n")
        with self.assertRaisesRegex(ValueError, "registered trusted"):
            harness.verify_bundle(self.output)
        self.assertFalse(marker.exists())
        path.write_bytes(original)
        schema = harness.load_json(self.output / "contract/schema.json")
        schema["additionalProperties"] = True
        harness.write_json(self.output / "contract/schema.json", schema)
        with self.assertRaisesRegex(ValueError, "registered trusted"):
            harness.verify_bundle(self.output)

    def test_valid_integers_with_long_zero_padding_match_task(self):
        data = b"0" * 5000 + b"1\n+" + b"0" * 5000 + b"8\n"
        result = subprocess.run([sys.executable, str(harness.SOURCES / "python/main.py")],
                                input=data, capture_output=True, timeout=5)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"1 8 64\n", result.stdout)

    def test_preflight_rejects_bad_selection_limits_and_outside_output(self):
        for languages, timeout, limit in (([], 1, 100), (["python", "python"], 1, 100), (["java"], 1, 100), (["python"], float("nan"), 100), (["python"], 0, 100), (["python"], 1, 0)):
            with self.subTest(languages=languages, timeout=timeout, limit=limit):
                with self.assertRaises(ValueError):
                    harness.run_harness(languages, self.output, timeout=timeout, output_limit=limit)
                self.assertFalse(self.output.exists())
        with self.assertRaises(ValueError):
            harness.run_harness(["python"], Path("/tmp/outside-harness-evidence"))

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        marker = self.output / "original"
        marker.write_text("keep")
        with self.assertRaises(FileExistsError):
            harness.run_harness(["python"], self.output)
        self.assertEqual([marker], list(self.output.iterdir()))

    def test_cli_works_from_an_external_directory_and_propagates_failure(self):
        source = self.sources("print('wrong')\n")
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run([sys.executable, str(ROOT / "scripts/language_harness.py"),
                                     "run", "--languages", "python", "--sources", str(source),
                                     "--output", str(self.output)], cwd=cwd, capture_output=True, timeout=10)
            self.assertEqual(1, result.returncode, result.stderr)
            verify = subprocess.run([sys.executable, str(ROOT / "scripts/language_harness.py"),
                                     "verify", str(self.output)], cwd=cwd, capture_output=True, timeout=10)
            self.assertEqual(0, verify.returncode, verify.stderr)
        self.assertEqual("failure", self.record()["trial"]["status"])


if __name__ == "__main__":
    unittest.main()
