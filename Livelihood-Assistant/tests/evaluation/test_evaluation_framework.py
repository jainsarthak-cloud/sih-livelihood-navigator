"""Phase 12 evaluation dataset and runner behavior tests."""

import json

import pytest

from app.evaluation.runner import load_records, metric, run_evaluation


def test_evaluation_runner_measures_all_categories_and_is_reproducible():
    first = run_evaluation()
    second = run_evaluation()

    assert first == second
    assert first["dataset"] == {
        "skill_normalization": 30, "recommendations": 12, "eligibility": 8,
        "opportunity_matching": 8, "roadmap_validity": 5,
    }
    assert first["skill_normalization"]["cases"] == 30
    assert first["skill_normalization"]["unknown_cases"] > 0
    assert first["recommendations"]["evaluated_cases"] > 0
    assert first["roadmap_validity"]["valid"] <= first["roadmap_validity"]["cases"]
    assert first["end_to_end_consistency"]["consistent"] == first["end_to_end_consistency"]["cases"]


def test_metric_calculation_and_unknown_correctness_are_reported():
    assert metric(2, 4) == {"cases": 4, "correct": 2, "accuracy": 0.5}
    report = run_evaluation()
    assert report["skill_normalization"]["unknown_correct"] == report["skill_normalization"]["unknown_cases"]


def test_invalid_labels_and_empty_dataset_fail_loudly(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        load_records(empty)

    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps([{
        "case_id": "x", "synthetic_evaluation": False, "rationale": "invalid",
        "input": {"value": 1}, "expected": {"result": "unknown"},
    }]), encoding="utf-8")
    with pytest.raises(ValueError, match="synthetic"):
        load_records(invalid)


def test_dataset_schema_requires_rationale_and_non_empty_expected_labels(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{
        "case_id": "x", "synthetic_evaluation": True, "input": {"value": 1}, "expected": {},
    }]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_records(path)


def test_dataset_requires_explicit_synthetic_evaluation_marker(tmp_path):
    path = tmp_path / "unmarked.json"
    path.write_text(json.dumps([{
        "case_id": "x", "rationale": "missing marker",
        "input": {"value": 1}, "expected": {"result": "unknown"},
    }]), encoding="utf-8")
    with pytest.raises(ValueError, match="explicitly declare"):
        load_records(path)
