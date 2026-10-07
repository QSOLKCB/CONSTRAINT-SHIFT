#!/usr/bin/env python3
"""Validate CONSTRAINT-SHIFT Phase 1 experiment records.

The JSON Schema is the structural source of truth. This module implements only
the Draft 2020-12 keywords used by the repository schema, then adds project
semantic checks that JSON Schema cannot conveniently express (cross-references,
ordered intervention sequence, unique factor/measurement names, and time order).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "experiment-record.schema.json"
EXAMPLE_DIR = ROOT / "schema" / "examples"
SUPPORTED_SCHEMA_VERSION = "2.0.0"
RFC3339_DATETIME = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt]"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?P<fraction>\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


class DuplicateKeyError(ValueError):
    pass


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _decimal_number(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"JSON number cannot be represented exactly: {value}") from exc


def load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(
        text,
        object_pairs_hook=_no_duplicate_keys,
        parse_float=_decimal_number,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-JSON numeric constant: {value}")
        ),
    )


def _typename(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, (float, Decimal)):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return (
            isinstance(value, int) and not isinstance(value, bool)
        ) or (
            isinstance(value, float) and math.isfinite(value) and value.is_integer()
        ) or (
            isinstance(value, Decimal)
            and value.is_finite()
            and value == value.to_integral_value()
        )
    if expected == "number":
        return (
            isinstance(value, int) and not isinstance(value, bool)
        ) or (
            isinstance(value, float) and math.isfinite(value)
        ) or (
            isinstance(value, Decimal) and value.is_finite()
        )
    return False


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported non-local $ref: {ref}")
    node: Any = root_schema
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"$ref does not resolve to an object: {ref}")
    return node


def _valid_datetime(value: str) -> bool:
    # fromisoformat also accepts compact dates, arbitrary separators, omitted
    # seconds, and non-colon offsets. Check the wire syntax before parsing dates.
    if RFC3339_DATETIME.fullmatch(value) is None:
        return False
    try:
        _parse_datetime(value)
    except ValueError:
        return False
    return True


def validate_schema_instance(
    value: Any,
    subschema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> list[str]:
    errors: list[str] = []

    if "$ref" in subschema:
        target = _resolve_ref(root_schema, subschema["$ref"])
        return validate_schema_instance(value, target, root_schema, path)

    if "const" in subschema and value != subschema["const"]:
        errors.append(f"{path}: must equal {subschema['const']!r}")

    if "enum" in subschema and value not in subschema["enum"]:
        errors.append(f"{path}: value {value!r} is not in the allowed enum")

    expected = subschema.get("type")
    if expected is not None:
        if not _is_type(value, expected):
            errors.append(
                f"{path}: expected {expected}, got {_typename(value)}"
            )
            return errors

    if isinstance(value, dict):
        required = subschema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")

        properties = subschema.get("properties", {})
        if subschema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")

        for key, child_schema in properties.items():
            if key in value:
                errors.extend(
                    validate_schema_instance(
                        value[key], child_schema, root_schema, f"{path}.{key}"
                    )
                )

    if isinstance(value, list):
        minimum = subschema.get("minItems")
        if minimum is not None and len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} item(s)")
        if subschema.get("uniqueItems"):
            seen: list[Any] = []
            for index, item in enumerate(value):
                if item in seen:
                    errors.append(f"{path}[{index}]: duplicate item")
                else:
                    seen.append(item)
        item_schema = subschema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    validate_schema_instance(
                        item, item_schema, root_schema, f"{path}[{index}]"
                    )
                )

    if isinstance(value, str):
        minimum = subschema.get("minLength")
        if minimum is not None and len(value) < minimum:
            errors.append(f"{path}: string shorter than {minimum}")
        pattern = subschema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            errors.append(f"{path}: string does not match required pattern")
        if subschema.get("format") == "date-time" and not _valid_datetime(value):
            errors.append(f"{path}: expected RFC 3339 date-time")

    if (
        isinstance(value, (int, float, Decimal))
        and not isinstance(value, bool)
        and "minimum" in subschema
        and value < subschema["minimum"]
    ):
        errors.append(f"{path}: value is below minimum {subschema['minimum']}")

    return errors


def _parse_datetime(value: str) -> tuple[int, str]:
    """Return an exact UTC ordering key: whole seconds and decimal fraction.

    Fraction strings without trailing zeros compare in numeric order, including
    arbitrarily many digits. Neither binary floats nor decimal context rounding
    participate in the comparison.
    """
    match = RFC3339_DATETIME.fullmatch(value)
    if match is None:
        raise ValueError("expected RFC 3339 date-time")
    fraction = match.group("fraction")
    whole = value
    if fraction is not None:
        whole = value[:match.start("fraction")] + value[match.end("fraction"):]
    parsed = datetime.fromisoformat(
        whole[:-1] + "+00:00" if whole.endswith(("Z", "z")) else whole
    )
    offset = parsed.utcoffset()
    assert offset is not None
    seconds = (
        parsed.toordinal() * 86400
        + parsed.hour * 3600 + parsed.minute * 60 + parsed.second
        - (offset.days * 86400 + offset.seconds)
    )
    return seconds, fraction[1:].rstrip("0") if fraction else ""


def validate_semantics(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    evidence = record.get("evidence", [])
    if not isinstance(evidence, list):
        return errors

    evidence_ids = [
        item.get("evidence_id")
        for item in evidence
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    ]
    if len(evidence_ids) != len(set(evidence_ids)):
        errors.append("$.evidence: evidence_id values must be unique")
    evidence_set = set(evidence_ids)

    refs: list[tuple[str, Any]] = []
    task = record.get("task")
    if isinstance(task, dict):
        refs.extend([
            ("$.task.specification_ref", task.get("specification_ref")),
            ("$.task.acceptance_ref", task.get("acceptance_ref")),
        ])
    agent = record.get("agent")
    if isinstance(agent, dict) and "instructions_ref" in agent:
        refs.append(("$.agent.instructions_ref", agent.get("instructions_ref")))
    toolchain = record.get("toolchain")
    if isinstance(toolchain, dict) and "dependency_lock_ref" in toolchain:
        refs.append(
            ("$.toolchain.dependency_lock_ref", toolchain.get("dependency_lock_ref"))
        )

    interventions = record.get("interventions")
    if isinstance(interventions, list):
        sequences = [
            item.get("sequence")
            for item in interventions
            if isinstance(item, dict) and _is_type(item.get("sequence"), "integer")
        ]
        if sequences and sequences != list(range(1, len(sequences) + 1)):
            errors.append(
                "$.interventions: sequence values must be contiguous and match "
                "array order starting at 1"
            )
        for index, item in enumerate(interventions):
            if isinstance(item, dict):
                for ref in item.get("evidence_refs", []):
                    refs.append((f"$.interventions[{index}].evidence_refs", ref))

    outcomes = record.get("verification_outcomes")
    if isinstance(outcomes, list):
        for index, item in enumerate(outcomes):
            if isinstance(item, dict):
                for ref in item.get("evidence_refs", []):
                    refs.append(
                        (f"$.verification_outcomes[{index}].evidence_refs", ref)
                    )

    for path, ref in refs:
        if isinstance(ref, str) and ref not in evidence_set:
            errors.append(f"{path}: unknown evidence reference {ref!r}")

    trial = record.get("trial")
    if isinstance(trial, dict):
        factors = trial.get("factors")
        if isinstance(factors, list):
            names = [
                item.get("name")
                for item in factors
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            ]
            if len(names) != len(set(names)):
                errors.append("$.trial.factors: factor names must be unique")

        measurements = trial.get("measurements")
        if isinstance(measurements, list):
            names = [
                item.get("name")
                for item in measurements
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            ]
            if len(names) != len(set(names)):
                errors.append(
                    "$.trial.measurements: measurement names must be unique"
                )

        started = trial.get("started_at")
        ended = trial.get("ended_at")
        if isinstance(started, str) and isinstance(ended, str):
            if _valid_datetime(started) and _valid_datetime(ended):
                if _parse_datetime(ended) < _parse_datetime(started):
                    errors.append("$.trial: ended_at must not precede started_at")

    return errors


def validate_record(
    record: Any,
    schema: dict[str, Any] | None = None,
) -> list[str]:
    if schema is None:
        schema = load_json(SCHEMA_PATH)
    if not isinstance(record, dict):
        return ["$: experiment record must be a JSON object"]
    if "schema_version" in record and record["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        return [
            "$.schema_version: unsupported version; expected "
            f"{SUPPORTED_SCHEMA_VERSION!r}"
        ]

    errors = validate_schema_instance(record, schema, schema)
    if not errors:
        errors.extend(validate_semantics(record))
    return errors


def validate_repo() -> list[str]:
    errors: list[str] = []
    try:
        schema = load_json(SCHEMA_PATH)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        DuplicateKeyError,
        ValueError,
    ) as exc:
        return [f"{SCHEMA_PATH.relative_to(ROOT)}: {exc}"]

    version = schema.get("properties", {}).get("schema_version", {}).get("const")
    if version != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            "schema version constant does not match validator-supported version "
            f"{SUPPORTED_SCHEMA_VERSION}"
        )

    examples = sorted(EXAMPLE_DIR.glob("*.json"))
    if not examples:
        errors.append("schema/examples: no Phase 1 example records found")

    for path in examples:
        try:
            record = load_json(path)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
            ValueError,
        ) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        for error in validate_record(record, schema):
            errors.append(f"{path.relative_to(ROOT)}: {error}")

    failed_path = EXAMPLE_DIR / "failed-trial.json"
    if not failed_path.is_file():
        errors.append(
            "schema/examples/failed-trial.json: required failure fixture missing"
        )
    else:
        try:
            failed = load_json(failed_path)
            trial = failed.get("trial") if isinstance(failed, dict) else None
            if not isinstance(trial, dict) or trial.get("status") != "failure":
                errors.append(
                    "schema/examples/failed-trial.json must remain an explicit "
                    "retained failure"
                )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
            ValueError,
        ):
            pass

    return errors


def main() -> int:
    errors = validate_repo()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Phase 1 experiment schema validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
