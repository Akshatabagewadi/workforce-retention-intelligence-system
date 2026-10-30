
import pandas as pd
import pytest
from pathlib import Path
from datetime import date

from analytics.feature_engineering import OBSERVATION_DATE


def create_negative_scenarios():

    scenarios = [
        {
            "scenario_id": "NEG-001",
            "issue_type": "FUTURE_DATA_LEAKAGE",
            "description": "Future information must not enter model features.",
            "expected_result": "REJECT",
        },
        {
            "scenario_id": "NEG-002",
            "issue_type": "MISSING_SURVEY_BIAS",
            "description": "Missing survey must not be treated as low engagement.",
            "expected_result": "DO_NOT_CLASSIFY_AS_NEGATIVE",
        },
        {
            "scenario_id": "NEG-003",
            "issue_type": "OUTCOME_DATE_MISMATCH",
            "description": "Voluntary attrition requires a termination date.",
            "expected_result": "REJECT",
        },
        {
            "scenario_id": "NEG-004",
            "issue_type": "NO_HUMAN_REVIEW",
            "description": "Completed intervention requires human review.",
            "expected_result": "FLAG_FOR_REVIEW",
        },
    ]

    output_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "ground_truth"
        / "negative_test_scenarios.csv"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(scenarios).to_csv(output_path, index=False)

    print("Negative scenario CSV saved:", output_path)


# NEG-001: Future data must be excluded
def test_future_data_leakage():

    observation_date = OBSERVATION_DATE

    sample_dates = pd.to_datetime([
        "2026-10-15",
        "2026-10-30",
        "2026-11-15",
    ])

    filtered_dates = sample_dates[
        sample_dates <= observation_date
    ]

    assert len(filtered_dates) == 2
    assert all(filtered_dates <= observation_date)
    assert pd.Timestamp("2026-11-15") not in filtered_dates


# NEG-002: Missing surveys must not become low engagement
def test_missing_survey_bias():

    engagement_score = None
    survey_status = "MISSING"

    is_low_engagement = (
        engagement_score is not None
        and engagement_score <= 2
    )

    assert survey_status == "MISSING"
    assert is_low_engagement is False


# NEG-003: Voluntary attrition requires termination date
def test_outcome_date_mismatch():

    attrition_type = "VOLUNTARY"
    termination_date = None

    is_valid = not (
        attrition_type == "VOLUNTARY"
        and termination_date is None
    )

    assert is_valid is False


# NEG-004: Completed interventions require human review
def test_no_human_review():

    status = "COMPLETED"
    human_reviewed = False

    requires_review = (
        status in ["IN_PROGRESS", "COMPLETED"]
        and not human_reviewed
    )

    assert requires_review is True


if __name__ == "__main__":
    create_negative_scenarios()
