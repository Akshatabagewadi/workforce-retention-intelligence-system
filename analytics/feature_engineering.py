
from pathlib import Path

import pandas as pd

from database.db import SessionLocal
from database.models import (
    Employee,
    TenureSnapshot,
    EngagementSurvey,
    WorkloadSnapshot,
    PromotionHistory,
)

# Prediction observation date
OBSERVATION_DATE = pd.Timestamp("2026-10-30")


def create_employee_features():

    db = SessionLocal()

    try:
        print("Loading employee data...")

        employees = pd.read_sql(
            db.query(Employee).statement, db.bind
        )

        tenure = pd.read_sql(
            db.query(TenureSnapshot).statement, db.bind
        )

        surveys = pd.read_sql(
            db.query(EngagementSurvey).statement, db.bind
        )

        workload = pd.read_sql(
            db.query(WorkloadSnapshot).statement, db.bind
        )

        promotions = pd.read_sql(
            db.query(PromotionHistory).statement, db.bind
        )

        print("Applying observation date filter...")

        # Convert date columns into datetime format.
        tenure["snapshot_date"] = pd.to_datetime(
            tenure["snapshot_date"]
        )

        surveys["survey_date"] = pd.to_datetime(
            surveys["survey_date"]
        )

        workload["snapshot_date"] = pd.to_datetime(
            workload["snapshot_date"]
        )

        promotions["promotion_date"] = pd.to_datetime(
            promotions["promotion_date"]
        )

        # IMPORTANT:
        # Use only information available on or before
        # the observation date.

        tenure = tenure[
            tenure["snapshot_date"] <= OBSERVATION_DATE
        ]

        surveys = surveys[
            surveys["survey_date"] <= OBSERVATION_DATE
        ]

        workload = workload[
            workload["snapshot_date"] <= OBSERVATION_DATE
        ]

        promotions = promotions[
            promotions["promotion_date"] <= OBSERVATION_DATE
        ]

        print("Calculating leakage-safe features...")

        # 1. TENURE FEATURES

        tenure = tenure.sort_values("snapshot_date")

        tenure_features = tenure.groupby("employee_id").agg(
            avg_tenure_months=("tenure_months", "mean"),
        ).reset_index()

        latest_tenure = (
            tenure.groupby("employee_id")
            .tail(1)[["employee_id", "tenure_months"]]
            .rename(
                columns={
                    "tenure_months": "latest_tenure_months"
                }
            )
        )

        tenure_features = tenure_features.merge(
            latest_tenure,
            on="employee_id",
            how="left"
        )

        # 2. ENGAGEMENT FEATURES

        # Only completed surveys are used for scores.
        completed_surveys = surveys[
            surveys["survey_status"] == "COMPLETED"
        ].copy()

        survey_features = completed_surveys.groupby(
            "employee_id"
        ).agg(
            avg_engagement=("engagement_score", "mean"),
            avg_satisfaction=("satisfaction_score", "mean"),
            avg_career_growth=("career_growth_score", "mean"),
            survey_count=("survey_id", "count"),
        ).reset_index()

        # Missing surveys are explicitly identified.
        survey_counts = surveys.groupby(
            "employee_id"
        ).size().reset_index(name="total_survey_records")

        survey_features = survey_features.merge(
            survey_counts,
            on="employee_id",
            how="outer"
        )

        # 3. WORKLOAD FEATURES

        workload_features = workload.groupby(
            "employee_id"
        ).agg(
            avg_weekly_hours=("weekly_hours", "mean"),
            avg_overtime_hours=("overtime_hours", "mean"),
            max_weekly_hours=("weekly_hours", "max"),
        ).reset_index()

        # 4. PROMOTION FEATURES

        promotion_features = promotions.groupby(
            "employee_id"
        ).size().reset_index(
            name="promotion_count"
        )

        # Calculate time since the latest promotion.
        latest_promotions = (
            promotions.groupby("employee_id")["promotion_date"]
            .max()
            .reset_index()
        )

        latest_promotions["months_since_promotion"] = (
            (OBSERVATION_DATE - latest_promotions["promotion_date"])
            .dt.days / 30.44
        )

        latest_promotions = latest_promotions[
            ["employee_id", "months_since_promotion"]
        ]

        promotion_features = promotion_features.merge(
            latest_promotions,
            on="employee_id",
            how="left"
        )

        # 5. MERGE ALL FEATURES

        # Keep only basic employee information.
        features = employees[
            [
                "employee_id",
                "role_id",
                "team_id",
                "hire_date",
            ]
        ].copy()

        features["hire_date"] = pd.to_datetime(
            features["hire_date"]
        )

        features["tenure_from_hire_months"] = (
            (OBSERVATION_DATE - features["hire_date"]).dt.days
            / 30.44
        )

        features = features.drop(columns=["hire_date"])

        feature_tables = [
            tenure_features,
            survey_features,
            workload_features,
            promotion_features,
        ]

        for table in feature_tables:
            features = features.merge(
                table,
                on="employee_id",
                how="left"
            )

        # 6. HANDLE MISSING VALUES

        features["promotion_count"] = (
            features["promotion_count"].fillna(0)
        )

        features["survey_count"] = (
            features["survey_count"].fillna(0)
        )

        features["total_survey_records"] = (
            features["total_survey_records"].fillna(0)
        )

        # Missing survey scores remain missing.
        # They are NOT replaced with low engagement scores.

        features["survey_missing"] = (
            features["total_survey_records"] == 0
        ).astype(int)

        # Employees with no promotion history.
        features["months_since_promotion"] = (
            features["months_since_promotion"].fillna(
                features["tenure_from_hire_months"]
            )
        )

        # 7. SAVE FEATURES

        output_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed"
            / "employee_features.csv"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        features.to_csv(
            output_path,
            index=False
        )

        print("\n================================")
        print("FEATURE ENGINEERING SUCCESSFUL")
        print("================================")

        print("Observation date:", OBSERVATION_DATE.date())
        print("Employees:", len(features))
        print("Features:", len(features.columns))
        print("Missing survey records:", int(
            features["survey_missing"].sum()
        ))
        print("Output:", output_path)

        return features

    except Exception as error:
        print("Feature engineering error:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_employee_features()
