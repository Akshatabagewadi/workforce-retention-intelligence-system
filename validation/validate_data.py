
from datetime import date
from pathlib import Path

from database.db import SessionLocal
from database.models import (
    Employee,
    Role,
    Team,
    TenureSnapshot,
    EngagementSurvey,
    WorkloadSnapshot,
    CompensationBand,
    PromotionHistory,
    AttritionOutcome,
    Intervention,
)

OBSERVATION_DATE = date(2026, 10, 30)
REPORT_PATH = Path("outputs/validation_report.txt")


# ==========================================
# FOUR NEGATIVE SCENARIO VALIDATION FUNCTIONS
# ==========================================

def check_future_data_leakage(record_date, observation_date):
    """Reject records dated after the observation date."""
    return record_date <= observation_date


def check_missing_survey_bias(engagement_score, survey_status):
    """Do not classify missing survey responses as low engagement."""
    if survey_status in ["MISSING", "PARTIAL"]:
        return False

    if engagement_score is None:
        return False

    return engagement_score <= 2


def check_outcome_date_mismatch(attrition_type, termination_date):
    """Voluntary attrition must have a termination date."""
    return (
        attrition_type == "VOLUNTARY"
        and termination_date is None
    )


def check_human_review(status, human_reviewed):
    """Flag completed or in-progress interventions without review."""
    return (
        status in ["IN_PROGRESS", "COMPLETED"]
        and not human_reviewed
    )


# ==========================================
# MAIN DATABASE VALIDATION
# ==========================================

def validate_data():

    db = SessionLocal()
    errors = []
    warnings = []
    report = []

    def log(message=""):
        print(message)
        report.append(str(message))

    try:

        log("\n================================")
        log("WORKFORCE DATA VALIDATION")
        log("================================")

        # 1. RECORD COUNTS

        models = [
            Employee,
            Role,
            Team,
            TenureSnapshot,
            EngagementSurvey,
            WorkloadSnapshot,
            CompensationBand,
            PromotionHistory,
            AttritionOutcome,
            Intervention,
        ]

        log("\n1. RECORD COUNTS")

        for model in models:
            count = db.query(model).count()
            log(f"{model.__tablename__}: {count}")

        # 2. EMPLOYEE VALIDATION

        log("\n2. EMPLOYEE VALIDATION")

        employee_ids = [
            row[0]
            for row in db.query(Employee.employee_id).all()
        ]

        if len(employee_ids) != len(set(employee_ids)):
            errors.append("Duplicate employee IDs found.")
        else:
            log("PASS: Employee IDs are unique.")

        missing_employees = db.query(Employee).filter(
            (Employee.role_id == None)
            | (Employee.team_id == None)
            | (Employee.hire_date == None)
        ).count()

        if missing_employees:
            errors.append(
                f"{missing_employees} employees have missing required fields."
            )
        else:
            log("PASS: Employee required fields are present.")

        # 3. FOREIGN KEY VALIDATION

        log("\n3. FOREIGN KEY VALIDATION")

        checks = [
            (
                "Employee -> Role",
                db.query(Employee).filter(
                    ~Employee.role_id.in_(
                        db.query(Role.role_id)
                    )
                ).count(),
            ),
            (
                "Employee -> Team",
                db.query(Employee).filter(
                    ~Employee.team_id.in_(
                        db.query(Team.team_id)
                    )
                ).count(),
            ),
            (
                "Tenure -> Employee",
                db.query(TenureSnapshot).filter(
                    ~TenureSnapshot.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
            (
                "Tenure -> Role",
                db.query(TenureSnapshot).filter(
                    ~TenureSnapshot.role_id.in_(
                        db.query(Role.role_id)
                    )
                ).count(),
            ),
            (
                "Tenure -> Team",
                db.query(TenureSnapshot).filter(
                    ~TenureSnapshot.team_id.in_(
                        db.query(Team.team_id)
                    )
                ).count(),
            ),
            (
                "Survey -> Employee",
                db.query(EngagementSurvey).filter(
                    ~EngagementSurvey.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
            (
                "Workload -> Employee",
                db.query(WorkloadSnapshot).filter(
                    ~WorkloadSnapshot.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
            (
                "Compensation -> Employee",
                db.query(CompensationBand).filter(
                    ~CompensationBand.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
            (
                "Promotion -> Employee",
                db.query(PromotionHistory).filter(
                    ~PromotionHistory.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
            (
                "Promotion -> Previous Role",
                db.query(PromotionHistory).filter(
                    ~PromotionHistory.previous_role_id.in_(
                        db.query(Role.role_id)
                    )
                ).count(),
            ),
            (
                "Promotion -> New Role",
                db.query(PromotionHistory).filter(
                    ~PromotionHistory.new_role_id.in_(
                        db.query(Role.role_id)
                    )
                ).count(),
            ),
            (
                "Intervention -> Employee",
                db.query(Intervention).filter(
                    ~Intervention.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
            (
                "Outcome -> Employee",
                db.query(AttritionOutcome).filter(
                    ~AttritionOutcome.employee_id.in_(
                        db.query(Employee.employee_id)
                    )
                ).count(),
            ),
        ]

        for name, count in checks:
            if count:
                errors.append(
                    f"{name}: {count} invalid relationships."
                )
            else:
                log(f"PASS: {name}")

        # 4. SURVEY VALIDATION

        log("\n4. SURVEY VALIDATION")

        invalid_surveys = db.query(EngagementSurvey).filter(
            (
                (EngagementSurvey.engagement_score < 1)
                | (EngagementSurvey.engagement_score > 5)
                | (EngagementSurvey.satisfaction_score < 1)
                | (EngagementSurvey.satisfaction_score > 5)
                | (EngagementSurvey.career_growth_score < 1)
                | (EngagementSurvey.career_growth_score > 5)
            )
        ).count()

        if invalid_surveys:
            errors.append(
                f"{invalid_surveys} surveys contain invalid scores."
            )
        else:
            log("PASS: Survey scores are within valid ranges.")

        missing_surveys = db.query(EngagementSurvey).filter(
            EngagementSurvey.survey_status.in_(
                ["MISSING", "PARTIAL"]
            )
        ).count()

        log(f"Missing or partial surveys: {missing_surveys}")

        # 5. DATE VALIDATION

        log("\n5. DATE VALIDATION")

        date_checks = [
            (
                "Surveys",
                db.query(EngagementSurvey).filter(
                    EngagementSurvey.survey_date > OBSERVATION_DATE
                ).count(),
            ),
            (
                "Workloads",
                db.query(WorkloadSnapshot).filter(
                    WorkloadSnapshot.snapshot_date > OBSERVATION_DATE
                ).count(),
            ),
            (
                "Tenure snapshots",
                db.query(TenureSnapshot).filter(
                    TenureSnapshot.snapshot_date > OBSERVATION_DATE
                ).count(),
            ),
        ]

        for name, count in date_checks:
            if count:
                errors.append(
                    f"{count} future {name.lower()} found."
                )
            else:
                log(f"PASS: No future {name.lower()}.")

        # 6. ATTRITION VALIDATION

        log("\n6. ATTRITION VALIDATION")

        invalid_outcomes = db.query(AttritionOutcome).filter(
            (
                (AttritionOutcome.termination_date != None)
                & (
                    AttritionOutcome.termination_date
                    > AttritionOutcome.horizon_end_date
                )
            )
            |
            (
                (AttritionOutcome.voluntary_attrition == True)
                & (AttritionOutcome.termination_date == None)
            )
            |
            (
                (AttritionOutcome.voluntary_attrition == False)
                & (AttritionOutcome.termination_date != None)
            )
        ).count()

        if invalid_outcomes:
            errors.append(
                f"{invalid_outcomes} inconsistent attrition outcomes."
            )
        else:
            log("PASS: Attrition outcomes are consistent.")

        # 7. INTERVENTION VALIDATION

        log("\n7. INTERVENTION VALIDATION")

        unreviewed = db.query(Intervention).filter(
            Intervention.human_reviewed == False,
            Intervention.status.in_(
                ["IN_PROGRESS", "COMPLETED"]
            ),
        ).count()

        if unreviewed:
            warnings.append(
                f"{unreviewed} active/completed interventions lack human review."
            )
        else:
            log(
                "PASS: No completed or in-progress intervention lacks review."
            )

        # 8. NEGATIVE SCENARIO RULE CHECKS

        log("\n8. NEGATIVE SCENARIO RULE CHECKS")

        negative_tests = [
            (
                "NEG-001 Future data leakage",
                check_future_data_leakage(
                    date(2026, 11, 15),
                    OBSERVATION_DATE,
                ) is False,
            ),
            (
                "NEG-002 Missing survey bias",
                check_missing_survey_bias(
                    None,
                    "MISSING",
                ) is False,
            ),
            (
                "NEG-003 Outcome date mismatch",
                check_outcome_date_mismatch(
                    "VOLUNTARY",
                    None,
                ) is True,
            ),
            (
                "NEG-004 No human review",
                check_human_review(
                    "COMPLETED",
                    False,
                ) is True,
            ),
        ]

        for name, passed in negative_tests:
            if passed:
                log(f"PASS: {name}")
            else:
                errors.append(
                    f"Negative scenario failed: {name}"
                )

        # 9. FINAL SUMMARY

        log("\n================================")
        log("VALIDATION SUMMARY")
        log("================================")

        log(f"Errors: {len(errors)}")
        log(f"Warnings: {len(warnings)}")

        for error in errors:
            log(f"ERROR: {error}")

        for warning in warnings:
            log(f"WARNING: {warning}")

        if not errors:
            log("\nDATA VALIDATION PASSED.")
        else:
            log("\nDATA VALIDATION FAILED.")

        # 10. SAVE REPORT

        REPORT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        REPORT_PATH.write_text(
            "\n".join(report),
            encoding="utf-8",
        )

        print(
            f"\nValidation report saved: {REPORT_PATH.resolve()}"
        )

    except Exception as error:
        db.rollback()
        print("Validation error:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    validate_data()
