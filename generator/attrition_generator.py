
import random
import hashlib
import json

from datetime import date, timedelta
from collections import defaultdict

from database.db import SessionLocal
from database.models import (
    Employee,
    EngagementSurvey,
    WorkloadSnapshot,
    PromotionHistory,
    AttritionOutcome,
)


# ==========================================
# CONFIGURATION
# ==========================================

SEED = 20261022

OBSERVATION_DATE = date(2026, 10, 30)
HORIZON_END_DATE = date(2027, 4, 30)

TARGET_ATTRITION_RATE = 0.10


# ==========================================
# GENERATE OUTCOMES IN MEMORY
# ==========================================

def generate_outcomes_data(db):

    rng = random.Random(SEED)

    employees = (
        db.query(Employee)
        .order_by(Employee.employee_id)
        .all()
    )

    if not employees:
        raise ValueError("No employees found.")

    print("Total employees:", len(employees))

    # Historical data only.

    surveys = db.query(EngagementSurvey).filter(
        EngagementSurvey.survey_date <= OBSERVATION_DATE
    ).all()

    workloads = db.query(WorkloadSnapshot).filter(
        WorkloadSnapshot.snapshot_date <= OBSERVATION_DATE
    ).all()

    promotions = db.query(PromotionHistory).filter(
        PromotionHistory.promotion_date <= OBSERVATION_DATE
    ).all()

    survey_data = defaultdict(list)
    workload_data = defaultdict(list)
    promotion_data = defaultdict(list)

    for survey in surveys:
        if survey.survey_status == "COMPLETED":
            survey_data[survey.employee_id].append(survey)

    for workload in workloads:
        workload_data[workload.employee_id].append(workload)

    for promotion in promotions:
        promotion_data[promotion.employee_id].append(promotion)

    print("Calculating employee risk scores...")

    employee_risks = []

    for employee in employees:

        employee_id = employee.employee_id
        score = 0

        # 1. Engagement signals

        employee_surveys = survey_data[employee_id]

        if employee_surveys:

            latest_survey = max(
                employee_surveys,
                key=lambda x: x.survey_date
            )

            if (
                latest_survey.engagement_score is not None
                and latest_survey.engagement_score <= 2
            ):
                score += 3

            if (
                latest_survey.career_growth_score is not None
                and latest_survey.career_growth_score <= 2
            ):
                score += 2

            if (
                latest_survey.satisfaction_score is not None
                and latest_survey.satisfaction_score <= 2
            ):
                score += 1

        # 2. Workload signals

        employee_workloads = workload_data[employee_id]

        if employee_workloads:

            average_overtime = sum(
                w.overtime_hours
                for w in employee_workloads
            ) / len(employee_workloads)

            average_hours = sum(
                w.weekly_hours
                for w in employee_workloads
            ) / len(employee_workloads)

            if average_overtime >= 8:
                score += 2

            if average_hours >= 48:
                score += 1

        # 3. Promotion signals

        employee_promotions = promotion_data[employee_id]

        recent_promotions = [
            p for p in employee_promotions
            if 0 <= (
                OBSERVATION_DATE - p.promotion_date
            ).days <= 730
        ]

        if not recent_promotions:
            score += 1

        employee_risks.append({
            "employee_id": employee_id,
            "score": score
        })

    # ======================================
    # DETERMINISTIC RANKING
    # ======================================

    employee_risks.sort(
        key=lambda item: (
            -item["score"],
            item["employee_id"]
        )
    )

    target_count = round(
        len(employees) * TARGET_ATTRITION_RATE
    )

    eligible_employees = [
        item for item in employee_risks
        if item["score"] > 0
    ]

    selected_employees = eligible_employees[:target_count]

    leaving_ids = {
        item["employee_id"]
        for item in selected_employees
    }

    # ======================================
    # CREATE OUTCOMES IN MEMORY
    # ======================================

    days = (
        HORIZON_END_DATE - OBSERVATION_DATE
    ).days

    outcomes = []

    for employee in employees:

        is_leaving = (
            employee.employee_id in leaving_ids
        )

        if is_leaving:

            termination_date = (
                OBSERVATION_DATE
                + timedelta(days=rng.randint(1, days))
            )

            attrition_type = "VOLUNTARY"
            voluntary_attrition = True

        else:

            termination_date = None
            attrition_type = "NONE"
            voluntary_attrition = False

        outcomes.append({
            "outcome_id": f"OUT-{employee.employee_id}",
            "employee_id": employee.employee_id,
            "observation_date": OBSERVATION_DATE.isoformat(),
            "horizon_end_date": HORIZON_END_DATE.isoformat(),
            "termination_date": (
                termination_date.isoformat()
                if termination_date else None
            ),
            "attrition_type": attrition_type,
            "voluntary_attrition": voluntary_attrition
        })

    return outcomes


# ==========================================
# GENERATE SHA-256 CHECKSUM
# ==========================================

def calculate_checksum(outcomes):

    serialized = json.dumps(
        outcomes,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


# ==========================================
# REPRODUCIBILITY TEST
# ==========================================

def test_reproducibility():

    db = SessionLocal()

    try:

        print("\nRunning first generation...")

        first_run = generate_outcomes_data(db)

        print("\nRunning second generation...")

        second_run = generate_outcomes_data(db)

        first_checksum = calculate_checksum(first_run)
        second_checksum = calculate_checksum(second_run)

        print("\n===================================")
        print("REPRODUCIBILITY TEST")
        print("===================================")

        print("First checksum:")
        print(first_checksum)

        print("\nSecond checksum:")
        print(second_checksum)

        if first_checksum == second_checksum:

            print("\nPASS: Both generations are identical.")

        else:

            print("\nFAIL: Generations are different.")

            raise AssertionError(
                "Reproducibility test failed."
            )

        print("\nTotal generated:", len(first_run))

        voluntary_count = sum(
            item["voluntary_attrition"]
            for item in first_run
        )

        print("Voluntary attrition:", voluntary_count)

        print(
            "Attrition rate:",
            round(
                voluntary_count / len(first_run) * 100,
                2
            ),
            "%"
        )

        print("\nExisting database was not modified.")

    finally:
        db.close()


# ==========================================
# OPTIONAL DATABASE WRITE
# ==========================================

def generate_attrition_outcomes():

    db = SessionLocal()

    try:

        outcomes = generate_outcomes_data(db)

        print(
            "\nWARNING: This operation replaces existing "
            "AttritionOutcome records."
        )

        confirmation = input(
            "Type REPLACE to continue: "
        )

        if confirmation != "REPLACE":

            print("Cancelled. Database was not modified.")
            return

        db.query(AttritionOutcome).delete(
            synchronize_session=False
        )

        for item in outcomes:

            db.add(
                AttritionOutcome(
                    outcome_id=item["outcome_id"],
                    employee_id=item["employee_id"],
                    observation_date=date.fromisoformat(
                        item["observation_date"]
                    ),
                    horizon_end_date=date.fromisoformat(
                        item["horizon_end_date"]
                    ),
                    termination_date=(
                        date.fromisoformat(item["termination_date"])
                        if item["termination_date"]
                        else None
                    ),
                    attrition_type=item["attrition_type"],
                    voluntary_attrition=item["voluntary_attrition"]
                )
            )

        db.commit()

        print("\nAttrition outcomes successfully generated.")

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    test_reproducibility()
