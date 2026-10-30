
import csv
from pathlib import Path
from datetime import date

from sqlalchemy import func

from database.db import SessionLocal
from database.models import (
    EngagementSurvey,
    WorkloadSnapshot,
    AttritionOutcome,
    Intervention,
)

OBSERVATION_DATE = date(2026, 10, 30)


def generate_anomaly_labels():

    db = SessionLocal()

    try:
        print("Loading latest employee surveys...")

        latest_dates = (
            db.query(
                EngagementSurvey.employee_id,
                func.max(EngagementSurvey.survey_date).label("latest_date")
            )
            .filter(EngagementSurvey.survey_date <= OBSERVATION_DATE)
            .group_by(EngagementSurvey.employee_id)
            .subquery()
        )

        surveys = (
            db.query(EngagementSurvey)
            .join(
                latest_dates,
                (EngagementSurvey.employee_id == latest_dates.c.employee_id)
                & (EngagementSurvey.survey_date == latest_dates.c.latest_date)
            )
            .all()
        )

        print("Loading latest workload records...")

        latest_workload_dates = (
            db.query(
                WorkloadSnapshot.employee_id,
                func.max(WorkloadSnapshot.snapshot_date).label("latest_date")
            )
            .filter(WorkloadSnapshot.snapshot_date <= OBSERVATION_DATE)
            .group_by(WorkloadSnapshot.employee_id)
            .subquery()
        )

        workloads = (
            db.query(WorkloadSnapshot)
            .join(
                latest_workload_dates,
                (WorkloadSnapshot.employee_id == latest_workload_dates.c.employee_id)
                & (WorkloadSnapshot.snapshot_date == latest_workload_dates.c.latest_date)
            )
            .all()
        )

        workload_map = {
            item.employee_id: item for item in workloads
        }

        print("Loading attrition and intervention records...")

        outcomes = db.query(AttritionOutcome).all()
        outcome_map = {item.employee_id: item for item in outcomes}

        interventions = db.query(Intervention).all()
        intervention_map = {}

        for item in interventions:
            intervention_map.setdefault(item.employee_id, []).append(item)

        print("Creating anomaly labels...")

        rows = []

        for survey in surveys:

            workload = workload_map.get(survey.employee_id)

            if workload is None:
                continue

            low_engagement = (
                survey.engagement_score is not None
                and survey.engagement_score <= 2
            )

            low_career_growth = (
                survey.career_growth_score is not None
                and survey.career_growth_score <= 2
            )

            high_overtime = workload.overtime_hours >= 10
            high_workload = workload.weekly_hours >= 50

            anomaly_count = sum([
                low_engagement,
                low_career_growth,
                high_overtime,
                high_workload,
            ])

            # Missing survey must not be interpreted as a negative score.
            missing_survey_bias = (
                survey.survey_status in ["MISSING", "PARTIAL"]
                and survey.engagement_score is None
            )

            # Future information must never be used in pre-outcome features.
            outcome = outcome_map.get(survey.employee_id)

            future_data_leakage = (
                outcome is not None
                and outcome.termination_date is not None
                and outcome.termination_date > OBSERVATION_DATE
            )

            # Check whether attrition type conflicts with termination date.
            outcome_date_mismatch = False

            if outcome is not None:
                if (
                    outcome.attrition_type in ["VOLUNTARY", "INVOLUNTARY"]
                    and outcome.termination_date is None
                ):
                    outcome_date_mismatch = True

                elif (
                    outcome.attrition_type == "NONE"
                    and outcome.termination_date is not None
                ):
                    outcome_date_mismatch = True

            # A planned recommendation without human review is not approval.
            employee_interventions = intervention_map.get(
                survey.employee_id, []
            )

            no_human_review = any(
                item.status in ["IN_PROGRESS", "COMPLETED"]
                and not item.human_reviewed
                for item in employee_interventions
            )

            issue_types = []

            if future_data_leakage:
                issue_types.append("FUTURE_DATA_LEAKAGE")

            if missing_survey_bias:
                issue_types.append("MISSING_SURVEY_BIAS")

            if outcome_date_mismatch:
                issue_types.append("OUTCOME_DATE_MISMATCH")

            if no_human_review:
                issue_types.append("NO_HUMAN_REVIEW")

            rows.append({
                "employee_id": survey.employee_id,
                "snapshot_date": str(OBSERVATION_DATE),
                "low_engagement": int(low_engagement),
                "low_career_growth": int(low_career_growth),
                "high_overtime": int(high_overtime),
                "high_workload": int(high_workload),
                "anomaly_count": anomaly_count,
                "is_anomaly": int(anomaly_count >= 2),
                "future_data_leakage": int(future_data_leakage),
                "missing_survey_bias": int(missing_survey_bias),
                "outcome_date_mismatch": int(outcome_date_mismatch),
                "no_human_review": int(no_human_review),
                "issue_type": "|".join(issue_types) if issue_types else "NONE",
            })

        output_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "ground_truth"
            / "anomaly_labels.csv"
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "employee_id",
            "snapshot_date",
            "low_engagement",
            "low_career_growth",
            "high_overtime",
            "high_workload",
            "anomaly_count",
            "is_anomaly",
            "future_data_leakage",
            "missing_survey_bias",
            "outcome_date_mismatch",
            "no_human_review",
            "issue_type",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print("\nANOMALY LABEL GENERATION COMPLETE")
        print("Employees labelled:", len(rows))
        print("Behavioral anomalies:", sum(row["is_anomaly"] for row in rows))
        print(
            "Future leakage labels:",
            sum(row["future_data_leakage"] for row in rows)
        )
        print(
            "Missing survey bias labels:",
            sum(row["missing_survey_bias"] for row in rows)
        )
        print(
            "Outcome date mismatch labels:",
            sum(row["outcome_date_mismatch"] for row in rows)
        )
        print(
            "No human review labels:",
            sum(row["no_human_review"] for row in rows)
        )
        print("Saved to:", output_path)

    except Exception as error:
        db.rollback()
        print("Error:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_anomaly_labels()
