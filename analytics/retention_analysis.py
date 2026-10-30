
from pathlib import Path

import pandas as pd

from database.db import SessionLocal
from database.models import (
    Employee,
    AttritionOutcome,
    Role,
    Team,
)


def run_retention_analysis():

    db = SessionLocal()

    try:
        print("Loading retention data...")

        employees = pd.read_sql(
            db.query(Employee).statement,
            db.bind
        )

        outcomes = pd.read_sql(
            db.query(AttritionOutcome).statement,
            db.bind
        )

        roles = pd.read_sql(
            db.query(Role).statement,
            db.bind
        )

        teams = pd.read_sql(
            db.query(Team).statement,
            db.bind
        )

        if outcomes.empty:
            print("No attrition outcomes found.")
            return

        # Overall retention metrics
        total_employees = len(outcomes)

        voluntary_leavers = outcomes[
            outcomes["voluntary_attrition"] == True
        ]

        attrition_count = len(voluntary_leavers)

        attrition_rate = (
            attrition_count / total_employees
        ) * 100

        retention_rate = 100 - attrition_rate

        print("\n========== RETENTION SUMMARY ==========")
        print("Total employees:", total_employees)
        print("Voluntary leavers:", attrition_count)
        print("Attrition rate:", round(attrition_rate, 2), "%")
        print("Retention rate:", round(retention_rate, 2), "%")

        # Department and role analysis
        employee_details = employees.merge(
            teams[["team_id", "department"]],
            on="team_id",
            how="left"
        )

        employee_details = employee_details.merge(
            roles[["role_id", "role_name"]],
            on="role_id",
            how="left"
        )

        analysis = employee_details.merge(
            outcomes[
                ["employee_id", "voluntary_attrition"]
            ],
            on="employee_id",
            how="left"
        )

        department_analysis = (
            analysis.groupby("department")
            .agg(
                employees=("employee_id", "count"),
                leavers=("voluntary_attrition", "sum")
            )
            .reset_index()
        )

        department_analysis["attrition_rate"] = (
            department_analysis["leavers"]
            / department_analysis["employees"]
            * 100
        )

        role_analysis = (
            analysis.groupby("role_name")
            .agg(
                employees=("employee_id", "count"),
                leavers=("voluntary_attrition", "sum")
            )
            .reset_index()
        )

        role_analysis["attrition_rate"] = (
            role_analysis["leavers"]
            / role_analysis["employees"]
            * 100
        )

        # Save reports
        output_folder = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed"
        )

        output_folder.mkdir(parents=True, exist_ok=True)

        department_analysis.to_csv(
            output_folder / "department_retention.csv",
            index=False
        )

        role_analysis.to_csv(
            output_folder / "role_retention.csv",
            index=False
        )

        print("\nDepartment analysis:")
        print(department_analysis.to_string(index=False))

        print("\nRole analysis:")
        print(role_analysis.to_string(index=False))

        print("\nRetention analysis completed!")
        print("Reports saved in data/processed/")

    finally:
        db.close()


if __name__ == "__main__":
    run_retention_analysis()
