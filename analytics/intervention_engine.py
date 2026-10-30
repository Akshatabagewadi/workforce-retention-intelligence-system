
from datetime import date
from pathlib import Path

import pandas as pd

from database.db import SessionLocal
from database.models import (
    Employee,
    EngagementSurvey,
    WorkloadSnapshot,
    PromotionHistory,
    Intervention,
)

OBSERVATION_DATE = date(2026, 10, 30)


def recommend_intervention(reasons):
    recommendations = []

    if (
        "High overtime" in reasons
        or "High working hours" in reasons
    ):
        recommendations.append(
            "Workload balancing and workload review"
        )

    if "Low engagement" in reasons:
        recommendations.append(
            "One-to-one manager engagement discussion"
        )

    if "Low career growth" in reasons:
        recommendations.append(
            "Career development and mentoring session"
        )

    if "Low satisfaction" in reasons:
        recommendations.append(
            "Employee feedback and wellbeing discussion"
        )

    if "No recent promotion" in reasons:
        recommendations.append(
            "Career progression review"
        )

    return recommendations


def get_next_intervention_number(db):
    """Find the next unused numeric intervention ID."""

    existing_ids = db.query(
        Intervention.intervention_id
    ).all()

    numbers = []

    for (intervention_id,) in existing_ids:
        parts = intervention_id.split("-")

        if (
            len(parts) == 3
            and parts[0] == "INT"
            and parts[1] == "2026"
            and parts[2].isdigit()
        ):
            numbers.append(int(parts[2]))

    return max(numbers, default=0) + 1


def generate_interventions():
    db = SessionLocal()

    try:
        print("Loading employee information...")

        employees = db.query(Employee).filter(
            Employee.employment_status == "ACTIVE"
        ).all()

        surveys = db.query(EngagementSurvey).filter(
            EngagementSurvey.survey_date <= OBSERVATION_DATE,
            EngagementSurvey.survey_status == "COMPLETED"
        ).all()

        workloads = db.query(WorkloadSnapshot).filter(
            WorkloadSnapshot.snapshot_date <= OBSERVATION_DATE
        ).all()

        promotions = db.query(PromotionHistory).filter(
            PromotionHistory.promotion_date <= OBSERVATION_DATE
        ).all()

        # Group survey records.
        survey_data = {}

        for survey in surveys:
            survey_data.setdefault(
                survey.employee_id, []
            ).append(survey)

        # Group workload records.
        workload_data = {}

        for workload in workloads:
            workload_data.setdefault(
                workload.employee_id, []
            ).append(workload)

        # Group promotion records.
        promotion_data = {}

        for promotion in promotions:
            promotion_data.setdefault(
                promotion.employee_id, []
            ).append(promotion)

        print("Calculating employee risk signals...")

        generated_count = 0
        skipped_count = 0

        # Get the next unique ID number.
        next_number = get_next_intervention_number(db)

        for employee in employees:

            employee_id = employee.employee_id
            reasons = []

            # 1. Latest completed engagement survey.
            employee_surveys = survey_data.get(
                employee_id, []
            )

            if employee_surveys:

                latest_survey = max(
                    employee_surveys,
                    key=lambda x: x.survey_date
                )

                if (
                    latest_survey.engagement_score is not None
                    and latest_survey.engagement_score <= 2
                ):
                    reasons.append("Low engagement")

                if (
                    latest_survey.career_growth_score is not None
                    and latest_survey.career_growth_score <= 2
                ):
                    reasons.append("Low career growth")

                if (
                    latest_survey.satisfaction_score is not None
                    and latest_survey.satisfaction_score <= 2
                ):
                    reasons.append("Low satisfaction")

            # 2. Average workload signals.
            employee_workloads = workload_data.get(
                employee_id, []
            )

            if employee_workloads:

                average_overtime = sum(
                    item.overtime_hours
                    for item in employee_workloads
                ) / len(employee_workloads)

                average_hours = sum(
                    item.weekly_hours
                    for item in employee_workloads
                ) / len(employee_workloads)

                if average_overtime >= 8:
                    reasons.append("High overtime")

                if average_hours >= 48:
                    reasons.append("High working hours")

            # 3. Recent promotion history.
            employee_promotions = promotion_data.get(
                employee_id, []
            )

            recent_promotions = [
                item for item in employee_promotions
                if 0 <= (
                    OBSERVATION_DATE - item.promotion_date
                ).days <= 730
            ]

            # No recent promotion alone is not a risk signal.
            if (
                not recent_promotions
                and "Low career growth" in reasons
            ):
                reasons.append("No recent promotion")

            # Do not flag employees without risk signals.
            if not reasons:
                continue

            recommendations = recommend_intervention(
                reasons
            )

            if not recommendations:
                continue

            # 4. Skip only active or completed recommendations.
            # Cancelled records remain in history but do not block
            # a new recommendation.
            existing = db.query(Intervention).filter(
                Intervention.employee_id == employee_id,
                Intervention.intervention_date == OBSERVATION_DATE,
                Intervention.status.in_([
                    "PLANNED",
                    "IN_PROGRESS",
                    "COMPLETED"
                ])
            ).first()

            if existing:
                skipped_count += 1
                continue

            # 5. Create a new unique intervention ID.
            intervention_id = (
                f"INT-2026-{next_number:06d}"
            )

            intervention = Intervention(
                intervention_id=intervention_id,
                employee_id=employee_id,
                intervention_date=OBSERVATION_DATE,
                intervention_type="; ".join(recommendations),
                status="PLANNED",
                reason="; ".join(reasons),
                human_reviewed=False,
            )

            db.add(intervention)

            generated_count += 1
            next_number += 1

            # Commit in batches.
            if generated_count % 500 == 0:
                db.commit()

                print(
                    "Interventions created:",
                    generated_count
                )

        db.commit()

        print("\n================================")
        print("INTERVENTION GENERATION COMPLETE")
        print("================================")

        print("Active employees:", len(employees))
        print("New recommendations:", generated_count)
        print("Existing recommendations skipped:", skipped_count)

        print("\nAll recommendations require human review.")

        # 6. Export all recommendations.
        records = db.query(Intervention).all()

        output = []

        for item in records:
            output.append({
                "intervention_id": item.intervention_id,
                "employee_id": item.employee_id,
                "intervention_date": item.intervention_date,
                "intervention_type": item.intervention_type,
                "reason": item.reason,
                "status": item.status,
                "human_reviewed": item.human_reviewed,
            })

        output_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed"
            / "intervention_recommendations.csv"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        pd.DataFrame(output).to_csv(
            output_path,
            index=False
        )

        print("\nCSV saved:", output_path)

    except Exception as error:
        db.rollback()
        print("Intervention generation error:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_interventions()
