
import random
import calendar
from datetime import date

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
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 20261022
REFERENCE_DATE = date(2026, 10, 30)
HISTORY_MONTHS = 24

random.seed(SEED)


# --------------------------------------------------
# GENERATE 24 MONTH-END DATES
# --------------------------------------------------

def monthly_dates():
    dates = []

    year = REFERENCE_DATE.year
    month = REFERENCE_DATE.month

    for _ in range(HISTORY_MONTHS):
        last_day = calendar.monthrange(year, month)[1]
        snapshot_date = date(year, month, last_day)

        # Do not generate dates after the reference date
        if snapshot_date > REFERENCE_DATE:
            snapshot_date = REFERENCE_DATE

        dates.append(snapshot_date)

        month -= 1
        if month == 0:
            month = 12
            year -= 1

    return sorted(dates)


# --------------------------------------------------
# GENERATE EMPLOYEE HISTORY
# --------------------------------------------------

def generate_employee_histories():

    db = SessionLocal()

    try:
        employees = db.query(Employee).all()
        roles = db.query(Role).all()
        teams = db.query(Team).all()

        if not employees:
            print("No employees found. Run master_data first.")
            return

        if not roles or not teams:
            print("Roles or teams are missing.")
            return

        # Prevent duplicate history generation
        existing = db.query(TenureSnapshot).first()

        if existing:
            print("Employee history already exists.")
            print("Skipping generation to prevent duplicate records.")
            return

        dates = monthly_dates()

        print("Starting employee history generation...")
        print("Employees:", len(employees))
        print("Monthly snapshots:", len(dates))

        survey_counter = 1
        workload_counter = 1
        promotion_counter = 1
        compensation_counter = 1

        for employee in employees:

            employee_role_id = employee.role_id
            employee_team_id = employee.team_id

            for snapshot_date in dates:

                # Skip dates before employee joined
                if employee.hire_date > snapshot_date:
                    continue

                tenure_months = (
                    (snapshot_date.year - employee.hire_date.year) * 12
                    + snapshot_date.month
                    - employee.hire_date.month
                )

                # ----------------------------------
                # TENURE SNAPSHOT
                # ----------------------------------

                snapshot_id = (
                    f"SNAP-{employee.employee_id}-"
                    f"{snapshot_date.year}{snapshot_date.month:02d}"
                )

                tenure = TenureSnapshot(
                    snapshot_id=snapshot_id,
                    employee_id=employee.employee_id,
                    role_id=employee_role_id,
                    team_id=employee_team_id,
                    snapshot_date=snapshot_date,
                    tenure_months=max(0, tenure_months),
                )

                db.add(tenure)

                # ----------------------------------
                # ENGAGEMENT SURVEY
                # ----------------------------------

                survey_status = random.choices(
                    ["COMPLETED", "MISSING", "PARTIAL"],
                    weights=[80, 10, 10],
                    k=1
                )[0]

                if survey_status == "COMPLETED":
                    engagement_score = random.randint(2, 5)
                    satisfaction_score = random.randint(2, 5)
                    career_growth_score = random.randint(2, 5)

                elif survey_status == "PARTIAL":
                    engagement_score = random.randint(2, 5)
                    satisfaction_score = None
                    career_growth_score = None

                else:
                    engagement_score = None
                    satisfaction_score = None
                    career_growth_score = None

                survey = EngagementSurvey(
                    survey_id=f"SURV-{survey_counter:08d}",
                    employee_id=employee.employee_id,
                    survey_date=snapshot_date,
                    engagement_score=engagement_score,
                    satisfaction_score=satisfaction_score,
                    career_growth_score=career_growth_score,
                    survey_status=survey_status,
                )

                db.add(survey)
                survey_counter += 1

                # ----------------------------------
                # WORKLOAD SNAPSHOT
                # ----------------------------------

                weekly_hours = random.randint(30, 55)
                overtime_hours = max(0, weekly_hours - 40)
                active_projects = random.randint(1, 5)

                workload = WorkloadSnapshot(
                    workload_id=f"WORK-{workload_counter:08d}",
                    employee_id=employee.employee_id,
                    snapshot_date=snapshot_date,
                    weekly_hours=weekly_hours,
                    overtime_hours=overtime_hours,
                    active_projects=active_projects,
                )

                db.add(workload)
                workload_counter += 1

                # ----------------------------------
                # COMPENSATION BAND
                # ----------------------------------

                band_number = random.randint(1, 5)

                compensation = CompensationBand(
                    compensation_id=f"COMP-{compensation_counter:08d}",
                    employee_id=employee.employee_id,
                    band_name=f"Band {band_number}",
                    minimum_salary=300000 * band_number,
                    maximum_salary=300000 * band_number + 199999,
                    effective_from=snapshot_date,
                    effective_to=None,
                )

                db.add(compensation)
                compensation_counter += 1

                # ----------------------------------
                # PROMOTION HISTORY
                # ----------------------------------

                # Small probability of promotion
                if random.random() < 0.01 and len(roles) > 1:

                    possible_roles = [
                        role for role in roles
                        if role.role_id != employee_role_id
                    ]

                    if possible_roles:
                        new_role = random.choice(possible_roles)

                        promotion = PromotionHistory(
                            promotion_id=f"PROM-{promotion_counter:08d}",
                            employee_id=employee.employee_id,
                            previous_role_id=employee_role_id,
                            new_role_id=new_role.role_id,
                            promotion_date=snapshot_date,
                            promotion_type="INTERNAL",
                        )

                        db.add(promotion)

                        employee_role_id = new_role.role_id
                        promotion_counter += 1

            # Commit after each employee
            db.commit()

        print("\nEmployee history generation completed!")
        print("Tenure snapshots:", db.query(TenureSnapshot).count())
        print("Engagement surveys:", db.query(EngagementSurvey).count())
        print("Workload snapshots:", db.query(WorkloadSnapshot).count())
        print("Compensation records:", db.query(CompensationBand).count())
        print("Promotion records:", db.query(PromotionHistory).count())

    except Exception as error:
        db.rollback()
        print("\nError generating employee history:")
        print(error)
        raise

    finally:
        db.close()


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    generate_employee_histories()
