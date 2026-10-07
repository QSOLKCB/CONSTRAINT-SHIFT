from pathlib import Path
import copy
import importlib.util
import tempfile
import unittest

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
