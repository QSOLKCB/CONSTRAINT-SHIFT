from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_phase1.py"

spec = importlib.util.spec_from_file_location("validate_phase1", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def example(name: str = "success.json") -> dict:
    return module.load_json(ROOT / "schema" / "examples" / name)


class Phase1SchemaTests(unittest.TestCase):
    def test_repository_schema_examples_pass(self) -> None:
        self.assertEqual([], module.validate_repo())

    def test_success_example_is_valid(self) -> None:
        self.assertEqual([], module.validate_record(example()))

    def test_failed_trial_is_valid_retained_evidence(self) -> None:
        record = example("failed-trial.json")
        self.assertEqual("failure", record["trial"]["status"])
        self.assertEqual([], module.validate_record(record))

    def test_schema_version_is_exact(self) -> None:
        record = example()
        record["schema_version"] = "1.1.0"
        errors = module.validate_record(record)
        self.assertTrue(any("$.schema_version" in error for error in errors), errors)

    def test_unknown_top_level_property_is_rejected(self) -> None:
        record = example()
        record["conclusion"] = "H2 proven"
        errors = module.validate_record(record)
        self.assertIn("$: unexpected property 'conclusion'", errors)

    def test_unknown_evidence_reference_is_rejected(self) -> None:
        record = example()
        record["verification_outcomes"][0]["evidence_refs"] = ["missing"]
        errors = module.validate_record(record)
        self.assertTrue(
            any("unknown evidence reference" in error for error in errors),
            errors,
        )

    def test_duplicate_evidence_id_is_rejected(self) -> None:
        record = example()
        duplicate = copy.deepcopy(record["evidence"][0])
        duplicate["path"] = "evidence/example/duplicate.txt"
        record["evidence"].append(duplicate)
        errors = module.validate_record(record)
        self.assertIn("$.evidence: evidence_id values must be unique", errors)

    def test_intervention_sequence_must_match_array_order(self) -> None:
        record = example()
        record["interventions"] = [
            {
                "sequence": 2,
                "actor": "human",
                "kind": "manual-edit",
                "description": "Synthetic intervention for validation.",
                "evidence_refs": ["verification-log"],
            }
        ]
        errors = module.validate_record(record)
        self.assertTrue(any("$.interventions" in error for error in errors), errors)

    def test_duplicate_factor_names_are_rejected(self) -> None:
        record = example()
        record["trial"]["factors"].append(
            {"name": "diagnostic_feedback", "value": "also-enabled"}
        )
        errors = module.validate_record(record)
        self.assertIn("$.trial.factors: factor names must be unique", errors)

    def test_duplicate_measurement_names_are_rejected(self) -> None:
        record = example()
        record["trial"]["measurements"].append(
            {"name": "wall_clock", "value": 3.0, "unit": "seconds"}
        )
        errors = module.validate_record(record)
        self.assertIn(
            "$.trial.measurements: measurement names must be unique",
            errors,
        )

    def test_end_before_start_is_rejected(self) -> None:
        record = example()
        record["trial"]["ended_at"] = "2026-10-07T02:39:59Z"
        errors = module.validate_record(record)
        self.assertIn("$.trial: ended_at must not precede started_at", errors)

    def test_boolean_is_not_an_integer_attempt(self) -> None:
        record = example()
        record["trial"]["attempt"] = True
        errors = module.validate_record(record)
        self.assertTrue(any("$.trial.attempt" in error for error in errors), errors)

    def test_parent_traversal_evidence_path_is_rejected(self) -> None:
        record = example()
        record["evidence"][0]["path"] = "../outside.txt"
        errors = module.validate_record(record)
        self.assertTrue(any("$.evidence[0].path" in error for error in errors), errors)

    def test_outside_evidence_paths_are_rejected_on_both_platforms(self) -> None:
        for path in (
            "/outside.txt", r"\outside.txt", r"C:\outside.txt",
            "C:/outside.txt", "c:outside.txt", r"\\server\share\outside.txt",
            "//server/share/outside.txt", r"..\outside.txt",
            "evidence/../outside.txt", r"evidence\..\outside.txt",
            r"evidence/..\outside.txt", r"evidence\../outside.txt",
            "evidence/..", r"evidence\..", "..",
        ):
            with self.subTest(path=path):
                record = example()
                record["evidence"][0]["path"] = path
                errors = module.validate_record(record)
                self.assertTrue(
                    any("$.evidence[0].path" in error for error in errors), errors,
                )

    def test_relative_evidence_paths_remain_valid(self) -> None:
        for path in ("evidence/log.txt", r"evidence\log.txt", "logs/run..txt"):
            with self.subTest(path=path):
                record = example()
                record["evidence"][0]["path"] = path
                self.assertEqual([], module.validate_record(record))

    def test_empty_verification_outcomes_are_rejected(self) -> None:
        record = example()
        record["verification_outcomes"] = []
        errors = module.validate_record(record)
        self.assertIn("$.verification_outcomes: expected at least 1 item(s)", errors)

    def test_every_verification_outcome_requires_evidence(self) -> None:
        statuses = module.load_json(module.SCHEMA_PATH)["$defs"]["verification"][
            "properties"
        ]["status"]["enum"]
        for status in statuses:
            for refs in (None, []):
                with self.subTest(status=status, refs=refs):
                    record = example()
                    outcome = record["verification_outcomes"][0]
                    outcome["status"] = status
                    if refs is None:
                        del outcome["evidence_refs"]
                    else:
                        outcome["evidence_refs"] = refs
                    errors = module.validate_record(record)
                    self.assertTrue(
                        any("$.verification_outcomes[0]" in error for error in errors),
                        errors,
                    )

    def test_not_run_outcome_with_retained_evidence_is_valid(self) -> None:
        record = example()
        record["verification_outcomes"][0]["status"] = "not_run"
        self.assertEqual([], module.validate_record(record))

    def test_non_rfc3339_timestamps_are_rejected_in_all_fields(self) -> None:
        for timestamp in (
            "2026-10-07 02:40:00Z", "2026-10-07T02:40Z",
            "2026-10-07T02:40:00+0000", "2026-10-07T02:40:00+00",
            "20261007T024000Z", "2026-W41-3T02:40:00Z",
            "2026-10-07T02:40:00,5Z", "2026-10-07T02:40:00+00:00:01",
            "2026-10-07T02:40:00+00:60", "2026-10-07T02:40:00+24:00",
            "2026-02-30T02:40:00Z", "2026-10-07T24:00:00Z",
            "2026-10-07T02:40:00", "2026-10-07T02:40:00Z\n",
        ):
            for field in ("created_at", "started_at", "ended_at"):
                with self.subTest(timestamp=timestamp, field=field):
                    record = example()
                    target = record if field == "created_at" else record["trial"]
                    target[field] = timestamp
                    errors = module.validate_record(record)
                    self.assertTrue(
                        any(field in error for error in errors), errors,
                    )

    def test_rfc3339_timestamps_remain_valid(self) -> None:
        for timestamp in (
            "2026-10-07T02:40:00Z", "2026-10-07t02:40:00z",
            "2026-10-07T02:40:00.123456789Z",
            "2026-10-07T13:10:00+10:30", "2026-10-06T22:40:00-04:00",
            "2026-10-07T02:40:00-00:00", "2024-02-29T02:40:00Z",
        ):
            with self.subTest(timestamp=timestamp):
                record = example()
                record["created_at"] = timestamp
                record["trial"]["started_at"] = timestamp
                record["trial"]["ended_at"] = timestamp
                self.assertEqual([], module.validate_record(record))

    def test_time_order_compares_offsets(self) -> None:
        record = example()
        record["trial"]["started_at"] = "2026-10-07T13:10:00+10:30"
        record["trial"]["ended_at"] = "2026-10-07t02:40:00z"
        self.assertEqual([], module.validate_record(record))
        record["trial"]["ended_at"] = "2026-10-07T02:39:59Z"
        self.assertIn(
            "$.trial: ended_at must not precede started_at",
            module.validate_record(record),
        )

    def test_integral_json_decimals_are_valid_in_all_integer_fields(self) -> None:
        record = example()
        record["trial"]["attempt"] = 1.0
        record["evidence"][0]["bytes"] = 0.0
        record["interventions"] = [
            {
                "sequence": 1.0,
                "actor": "human",
                "kind": "manual-edit",
                "description": "Synthetic intervention for validation.",
                "evidence_refs": ["verification-log"],
            }
        ]
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "integral.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual([], module.validate_record(module.load_json(path)))
        record["interventions"][0]["sequence"] = 2.0
        errors = module.validate_record(record)
        self.assertTrue(any("$.interventions: sequence" in e for e in errors), errors)

    def test_non_integral_and_non_finite_values_are_not_integers(self) -> None:
        for value in (1.5, True, False, float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                record = example()
                record["trial"]["attempt"] = value
                errors = module.validate_record(record)
                self.assertTrue(any("$.trial.attempt" in e for e in errors), errors)
        record = example()
        record["trial"]["attempt"] = 0.0
        self.assertIn(
            "$.trial.attempt: value is below minimum 1", module.validate_record(record),
        )

    def test_missing_failure_fixture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tempdir:
            examples = Path(tempdir)
            (examples / "success.json").write_text(
                json.dumps(example()), encoding="utf-8",
            )
            with patch.object(module, "EXAMPLE_DIR", examples):
                errors = module.validate_repo()
        self.assertTrue(any("failed-trial.json" in e for e in errors), errors)

    def test_failure_fixture_requires_explicit_failure(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tempdir:
            examples = Path(tempdir)
            (examples / "failed-trial.json").write_text(
                json.dumps(example()), encoding="utf-8",
            )
            with patch.object(module, "EXAMPLE_DIR", examples):
                errors = module.validate_repo()
        self.assertTrue(any("explicit retained failure" in e for e in errors), errors)

    def test_loader_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "duplicate.json"
            path.write_text(
                '{"schema_version":"1.0.0","schema_version":"1.0.0"}'
            )
            with self.assertRaises(module.DuplicateKeyError):
                module.load_json(path)

    def test_loader_rejects_non_json_numeric_constants(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "nan.json"
            path.write_text('{"value":NaN}')
            with self.assertRaises(ValueError):
                module.load_json(path)


if __name__ == "__main__":
    unittest.main()
