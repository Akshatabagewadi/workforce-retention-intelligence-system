
import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    balanced_accuracy_score,
)

from database.db import SessionLocal
from database.models import AttritionOutcome


SEED = 20261022


# ==========================================
# EXPLAIN EMPLOYEE SIGNALS
# ==========================================

def explain_employee(row):

    reasons = []

    if (
        pd.notna(row.get("avg_engagement"))
        and row["avg_engagement"] <= 2
    ):
        reasons.append("Low average engagement")

    if (
        pd.notna(row.get("avg_career_growth"))
        and row["avg_career_growth"] <= 2
    ):
        reasons.append("Low career growth")

    if (
        pd.notna(row.get("avg_satisfaction"))
        and row["avg_satisfaction"] <= 2
    ):
        reasons.append("Low satisfaction")

    if (
        pd.notna(row.get("avg_overtime_hours"))
        and row["avg_overtime_hours"] >= 8
    ):
        reasons.append("High average overtime")

    if (
        pd.notna(row.get("avg_weekly_hours"))
        and row["avg_weekly_hours"] >= 48
    ):
        reasons.append("High average weekly workload")

    if (
        pd.notna(row.get("months_since_promotion"))
        and row["months_since_promotion"] >= 24
        and pd.notna(row.get("avg_career_growth"))
        and row["avg_career_growth"] <= 2
    ):
        reasons.append("Limited recent career progression")

    if not reasons:
        return "No flagged supportive signals"

    return ", ".join(reasons)


# ==========================================
# TRAIN ATTRITION MODEL
# ==========================================

def train_attrition_model():

    db = SessionLocal()

    try:

        print("\nLoading employee features...")

        base_path = Path(__file__).resolve().parent.parent

        features_path = (
            base_path
            / "data"
            / "processed"
            / "employee_features.csv"
        )

        output_path = (
            base_path
            / "data"
            / "processed"
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        if not features_path.exists():
            raise FileNotFoundError(
                "Employee features not found. "
                "Run feature engineering first."
            )

        features = pd.read_csv(features_path)

        outcomes = pd.read_sql(
            db.query(AttritionOutcome).statement,
            db.bind
        )

        # Check duplicate IDs

        if features["employee_id"].duplicated().any():
            raise ValueError(
                "Duplicate employee IDs in feature data."
            )

        if outcomes["employee_id"].duplicated().any():
            raise ValueError(
                "Duplicate employee IDs in outcome data."
            )

        print("Combining features and outcomes...")

        data = features.merge(
            outcomes[
                [
                    "employee_id",
                    "observation_date",
                    "horizon_end_date",
                    "termination_date",
                    "voluntary_attrition",
                ]
            ],
            on="employee_id",
            how="inner",
            validate="one_to_one"
        )

        if data.empty:
            raise ValueError(
                "No matching employee outcomes found."
            )

        # ======================================
        # DATE VALIDATION
        # ======================================

        for column in [
            "observation_date",
            "horizon_end_date",
            "termination_date",
        ]:
            data[column] = pd.to_datetime(
                data[column],
                errors="coerce"
            )

        if not (
            data["observation_date"]
            <= data["horizon_end_date"]
        ).all():
            raise ValueError(
                "Invalid observation and horizon dates."
            )

        invalid_termination = (
            data["termination_date"].notna()
            & (
                (
                    data["termination_date"]
                    <= data["observation_date"]
                )
                |
                (
                    data["termination_date"]
                    > data["horizon_end_date"]
                )
            )
        )

        if invalid_termination.any():
            raise ValueError(
                "Termination dates outside prediction horizon."
            )

        # ======================================
        # PREPARE FEATURES AND TARGET
        # ======================================

        y = data["voluntary_attrition"].astype(int)

        excluded_columns = [
            "employee_id",
            "observation_date",
            "horizon_end_date",
            "termination_date",
            "voluntary_attrition",
        ]

        X = data.drop(
            columns=excluded_columns,
            errors="ignore"
        )

        X = X.dropna(
            axis=1,
            how="all"
        )

        numeric_columns = X.select_dtypes(
            include=["number", "bool"]
        ).columns.tolist()

        categorical_columns = X.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if not numeric_columns and not categorical_columns:
            raise ValueError(
                "No usable model features found."
            )

        # ======================================
        # PREPROCESSING
        # ======================================

        numeric_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="median")
            ),
            (
                "scaler",
                StandardScaler()
            ),
        ])

        categorical_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="most_frequent")
            ),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore")
            ),
        ])

        transformers = []

        if numeric_columns:
            transformers.append(
                (
                    "numeric",
                    numeric_pipeline,
                    numeric_columns
                )
            )

        if categorical_columns:
            transformers.append(
                (
                    "categorical",
                    categorical_pipeline,
                    categorical_columns
                )
            )

        preprocessing = ColumnTransformer(
            transformers=transformers
        )

        model = Pipeline([
            (
                "preprocessing",
                preprocessing
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    min_samples_leaf=5,
                    random_state=SEED,
                    class_weight="balanced"
                )
            ),
        ])

        # ======================================
        # TRAIN AND TEST SPLIT
        # ======================================

        print("Splitting training and testing data...")

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=SEED,
            stratify=y
        )

        print("Training Random Forest model...")

        model.fit(
            X_train,
            y_train
        )

        predictions = model.predict(X_test)

        positive_class_index = list(
            model.classes_
        ).index(1)

        probabilities = model.predict_proba(
            X_test
        )[:, positive_class_index]

        # ======================================
        # MODEL EVALUATION
        # ======================================

        accuracy = accuracy_score(
            y_test,
            predictions
        )

        precision = precision_score(
            y_test,
            predictions,
            zero_division=0
        )

        recall = recall_score(
            y_test,
            predictions,
            zero_division=0
        )

        f1 = f1_score(
            y_test,
            predictions,
            zero_division=0
        )

        balanced_accuracy = balanced_accuracy_score(
            y_test,
            predictions
        )

        roc_auc = roc_auc_score(
            y_test,
            probabilities
        )

        pr_auc = average_precision_score(
            y_test,
            probabilities
        )

        print("\n========== MODEL EVALUATION ==========")

        print("Total employees:", len(data))
        print("Training records:", len(X_train))
        print("Testing records:", len(X_test))

        print("Accuracy:", round(accuracy, 4))
        print("Balanced Accuracy:", round(balanced_accuracy, 4))
        print("Precision:", round(precision, 4))
        print("Recall:", round(recall, 4))
        print("F1 Score:", round(f1, 4))
        print("ROC-AUC:", round(roc_auc, 4))
        print("PR-AUC:", round(pr_auc, 4))

        print("\nClassification Report:")

        print(
            classification_report(
                y_test,
                predictions,
                zero_division=0
            )
        )

        matrix = confusion_matrix(
            y_test,
            predictions
        )

        print("\nConfusion Matrix:")
        print(matrix)

        # ======================================
        # SAVE CONFUSION MATRIX
        # ======================================

        pd.DataFrame(
            matrix,
            index=[
                "Actual Retained",
                "Actual Attrition"
            ],
            columns=[
                "Predicted Retained",
                "Predicted Attrition"
            ]
        ).to_csv(
            output_path / "confusion_matrix.csv"
        )

        # ======================================
        # FEATURE IMPORTANCE
        # ======================================

        classifier = model.named_steps[
            "classifier"
        ]

        feature_names = (
            model.named_steps["preprocessing"]
            .get_feature_names_out()
        )

        importance = pd.DataFrame({
            "feature": feature_names,
            "importance": classifier.feature_importances_,
        }).sort_values(
            by="importance",
            ascending=False
        )

        importance.to_csv(
            output_path / "feature_importance.csv",
            index=False
        )

        print("\n========== TOP 10 IMPORTANT FEATURES ==========")

        print(
            importance.head(10).to_string(index=False)
        )

        # ======================================
        # SAVE TRAINED MODEL
        # ======================================

        model_path = (
            output_path / "retention_model.joblib"
        )

        joblib.dump(
            model,
            model_path
        )

        print("\nTrained model saved:", model_path)

        # ======================================
        # GENERATE ALL EMPLOYEE RISK SCORES
        # ======================================

        print("\nGenerating employee retention scores...")

        all_probabilities = model.predict_proba(
            X
        )[:, positive_class_index]

        risk_report = data[
            ["employee_id"]
        ].copy()

        risk_report["risk_score_pct"] = (
            all_probabilities * 100
        ).round(2)

        # These are configurable demonstration thresholds.
        risk_report["risk_category"] = pd.cut(
            risk_report["risk_score_pct"],
            bins=[-0.01, 30, 60, 100],
            labels=["LOW", "MEDIUM", "HIGH"]
        ).astype(str)

        # Add rule-based explanations from source features.
        explanations = X.copy()

        explanations["employee_id"] = (
            data["employee_id"].values
        )

        risk_report["explainable_signals"] = (
            explanations.apply(
                explain_employee,
                axis=1
            ).values
        )

        risk_report["signal_count"] = (
            risk_report["explainable_signals"].apply(
                lambda value: (
                    0
                    if value == "No flagged supportive signals"
                    else len(value.split(", "))
                )
            )
        )

        risk_report["recommended_support"] = (
            risk_report["explainable_signals"].apply(
                lambda value: (
                    "No immediate action indicated; "
                    "continue regular check-ins"
                    if value == "No flagged supportive signals"
                    else
                    "Offer a supportive HR conversation "
                    "and review workload or career support"
                )
            )
        )

        risk_report = risk_report.sort_values(
            "risk_score_pct",
            ascending=False
        )

        risk_report_path = (
            output_path / "employee_risk_scores.csv"
        )

        risk_report.to_csv(
            risk_report_path,
            index=False
        )

        print("\n========== EMPLOYEE RISK SUMMARY ==========")

        print(
            risk_report["risk_category"]
            .value_counts()
            .to_string()
        )

        print("\nSample employee risk scores:")

        print(
            risk_report.head(10).to_string(index=False)
        )

        print(
            "\nEmployee risk report saved:",
            risk_report_path
        )

        # ======================================
        # SAVE METRICS
        # ======================================

        metrics = {
            "model": "Random Forest",
            "total_employees": int(len(data)),
            "training_records": int(len(X_train)),
            "testing_records": int(len(X_test)),
            "accuracy": float(accuracy),
            "balanced_accuracy": float(balanced_accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "random_seed": SEED,
            "evaluation_type": "Random employee holdout",
            "risk_score_thresholds": {
                "low": "0-30",
                "medium": "Above 30-60",
                "high": "Above 60-100"
            },
            "risk_score_note": (
                "Random Forest model score, not a calibrated "
                "real-world attrition probability."
            ),
        }

        with open(
            output_path / "model_metrics.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                metrics,
                file,
                indent=4
            )

        print("\n========== OUTPUT FILES ==========")

        print("1. model_metrics.json")
        print("2. confusion_matrix.csv")
        print("3. feature_importance.csv")
        print("4. retention_model.joblib")
        print("5. employee_risk_scores.csv")

        print(
            "\nIMPORTANT: This model learns from synthetic "
            "rule-generated labels. Its scores are not validated "
            "real-world employee attrition probabilities. "
            "Risk categories are supportive review indicators, "
            "not automated employment decisions."
        )

    finally:
        db.close()


if __name__ == "__main__":
    train_attrition_model()
