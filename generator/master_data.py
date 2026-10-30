
import random
from datetime import date, timedelta

from database.db import SessionLocal
from database.models import Employee, Role, Team

SEED = 20261022
EMPLOYEE_COUNT = 10000

REFERENCE_DATE = date(2026, 10, 30)

ROLES = [
    ("ROLE-001", "Software Engineer", "LEVEL-2"),
    ("ROLE-002", "Senior Software Engineer", "LEVEL-3"),
    ("ROLE-003", "Data Analyst", "LEVEL-2"),
    ("ROLE-004", "Data Scientist", "LEVEL-3"),
    ("ROLE-005", "Product Manager", "LEVEL-4"),
    ("ROLE-006", "Business Analyst", "LEVEL-2"),
    ("ROLE-007", "QA Engineer", "LEVEL-2"),
    ("ROLE-008", "DevOps Engineer", "LEVEL-3"),
    ("ROLE-009", "Technical Lead", "LEVEL-4"),
    ("ROLE-010", "HR Analyst", "LEVEL-2"),
]

TEAMS = [
    ("TEAM-001", "Engineering", "Technology"),
    ("TEAM-002", "Data Analytics", "Technology"),
    ("TEAM-003", "Data Science", "Technology"),
    ("TEAM-004", "Product", "Product"),
    ("TEAM-005", "Quality Assurance", "Technology"),
    ("TEAM-006", "DevOps", "Technology"),
    ("TEAM-007", "Human Resources", "HR"),
    ("TEAM-008", "Business Analysis", "Business"),
    ("TEAM-009", "Platform", "Technology"),
    ("TEAM-010", "Operations", "Operations"),
]


def generate_master_data():
    random.seed(SEED)

    db = SessionLocal()

    try:
        # Prevent duplicate master data during reruns.
        existing = db.query(Employee).first()

        if existing:
            print("Master data already exists.")
            print("No duplicate records created.")
            return

        # Create roles
        for role_id, role_name, level in ROLES:
            db.add(Role(
                role_id=role_id,
                role_name=role_name,
                job_level=level
            ))

        # Create teams
        for team_id, team_name, department in TEAMS:
            db.add(Team(
                team_id=team_id,
                team_name=team_name,
                department=department
            ))

        db.flush()

        # Generate employees
        start_date = date(2016, 10, 30)
        total_days = (REFERENCE_DATE - start_date).days

        for i in range(1, EMPLOYEE_COUNT + 1):

            employee_id = f"EMP-{i:06d}"

            hire_date = start_date + timedelta(
                days=random.randint(0, total_days)
            )

            role_id = random.choice(ROLES)[0]
            team_id = random.choice(TEAMS)[0]

            employee = Employee(
                employee_id=employee_id,
                role_id=role_id,
                team_id=team_id,
                hire_date=hire_date,
                employment_status="ACTIVE"
            )

            db.add(employee)

        db.commit()

        print("Master data generated successfully!")
        print("Employees:", db.query(Employee).count())
        print("Roles:", db.query(Role).count())
        print("Teams:", db.query(Team).count())

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_master_data()
