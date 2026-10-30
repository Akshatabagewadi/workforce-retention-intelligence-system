# Workforce Retention Intelligence System

**Explainable AI-Powered Employee Engagement & Retention Analytics Platform**

## 1. Project Overview

The Workforce Retention Intelligence System is an AI-powered analytics platform designed to analyze employee engagement, workload, career growth and retention patterns.

It uses machine learning to generate employee-level retention risk scores and explainable supporting signals. HR teams can use these insights to identify areas where employees may benefit from additional support.

The platform uses synthetic employee data covering 24 months and provides an interactive Streamlit dashboard.

## 2. Project Objectives

- Analyze employee engagement and satisfaction.
- Identify workload and career-growth patterns.
- Predict synthetic employee attrition outcomes.
- Generate individual employee risk scores.
- Provide explainable supporting signals.
- Support human-reviewed HR interventions.
- Maintain reproducible and leakage-aware data processing.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Database | SQLite |
| Database ORM | SQLAlchemy |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Model | Random Forest Classifier |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |
| Model Persistence | Joblib |

## 4. Dataset Overview

The project contains synthetic employee histories covering 24 months.

| Entity | Records |
|---|---:|
| Employees | 10,000 |
| Roles | 10 |
| Teams | 10 |
| Tenure Snapshots | 217,275 |
| Engagement Surveys | 217,275 |
| Workload Snapshots | 217,275 |
| Compensation Bands | 217,275 |
| Promotion History | 2,165 |
| Attrition Outcomes | 10,000 |
| Interventions | 8,268 |

**Total database records: 899,553**

- Random seed: `20261022`
- Observation date: `2026-10-30`
- Prediction horizon end: `2027-04-30`
- Synthetic voluntary attrition rate: 10%

## 5. Machine Learning

The platform uses a Random Forest Classifier.

### Features considered

- Employee tenure
- Engagement score
- Satisfaction score
- Career growth score
- Weekly working hours
- Overtime hours
- Promotion history
- Time since last promotion

### Model evaluation

| Metric | Result |
|---|---:|
| Accuracy | 61.65% |
| Balanced Accuracy | 55.58% |
| Precision | 12.65% |
| Recall | 48.00% |
| F1 Score | 20.02% |
| ROC-AUC | 0.6273 |
| PR-AUC | 0.2071 |

The model is trained and evaluated using synthetic, rule-generated labels. These results measure performance on the simulated dataset and do not establish real-world employee attrition prediction accuracy.

## 6. Explainability

The platform displays transparent supporting signals such as:

- Low engagement
- Low career growth
- Low satisfaction
- High overtime
- High weekly workload
- Limited recent career progression

These rule-based signals are not causal explanations of the Random Forest model's individual predictions.

## 7. Dashboard Features

The Streamlit dashboard includes:

1. Workforce Overview
2. Retention Distribution
3. Department-wise Attrition
4. Role-wise Workforce Analysis
5. Employee Engagement Insights
6. Workload Insights
7. AI-Generated Employee Retention Risk
8. HR Intervention Tracking
9. Employee Information
10. Download Reports

## 8. Project Structure

```text
Workforce-Retention-Intelligence/
│
├── analytics/
│   ├── evaluation.py
│   └── feature_engineering.py
│
├── dashboard/
│   └── app.py
│
├── database/
│   ├── db.py
│   └── models.py
│
├── generator/
│   ├── attrition_generator.py
│   └── export_data.py
│
├── validation/
│   └── validate_data.py
│
├── tests/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── ground_truth/
│
├── outputs/
│   ├── validation_report.txt
│   └── exports/
│
├── docs/
│
├── init_db.py
├── requirements.txt
└── README.md
```

## 9. Installation and Setup

### Prerequisites

- Python 3.11 or later
- pip
- Git

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_PROJECT_FOLDER
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Initialize the database

Only when creating a fresh database:

```bash
python init_db.py
```

### Step 6: Generate employee features

```bash
python -m analytics.feature_engineering
```

### Step 7: Train and evaluate the model

```bash
python -m analytics.evaluation
```

### Step 8: Generate exports

```bash
python -m generator.export_data
```

### Step 9: Run validation

```bash
python -m validation.validate_data
```

### Step 10: Test reproducibility

```bash
python -m generator.attrition_generator
```

This command runs the safe in-memory reproducibility test. It does not modify existing database records.

### Step 11: Launch dashboard

```bash
python -m streamlit run dashboard/app.py
```

## 10. Generated Model Outputs

The model generates:

- `retention_model.joblib`
- `employee_risk_scores.csv`
- `feature_importance.csv`
- `confusion_matrix.csv`
- `model_metrics.json`

## 11. Data Exports

The export script generates CSV and JSON files for all ten database tables, together with:

- `workforce_seed.sql`
- `source_manifest.json`
- `validation_summary.txt`

The SHA-256 checksums in the source manifest help verify exported file integrity.

## 12. Validation and Reproducibility

The validation process checks:

- Employee ID uniqueness
- Required employee fields
- Foreign-key relationships
- Survey score ranges
- Missing survey handling
- Future data leakage
- Attrition outcome consistency
- Human-review requirements
- Four negative scenario rules

The reproducibility test generates outcomes twice using seed `20261022` and compares SHA-256 checksums.

## 13. Responsible AI and Limitations

This project uses entirely synthetic data and simulated attrition labels.

The model scores are not calibrated real-world probabilities. Risk categories and supporting signals are intended for demonstration and supportive HR review only.

The platform must not make automated hiring, firing, promotion or other employment decisions.

Human review and contextual assessment are necessary before any intervention.

## 14. Future Enhancements

- Temporal model validation
- SHAP-based individual model explanations
- Human-review workflow
- Intervention outcome tracking
- Model calibration and fairness evaluation
- Automated reproducibility and integration tests
- Improved reporting and deployment


