# Workforce Retention Intelligence System

## Explainable AI-Powered Employee Engagement & Retention Analytics Platform

## 1. Project Overview

The Workforce Retention Intelligence System is an AI-powered analytics platform designed to analyze employee engagement, workload, career growth, and retention patterns.

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

All employee records and outcomes are synthetic and generated for demonstration purposes.

## 5. Machine Learning

The platform uses a Random Forest Classifier to identify patterns associated with synthetic employee attrition outcomes.

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
workforce-retention-intelligence-system/
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
│   ├── init_db.py
│   ├── master_data.py
│   ├── data_generator.py
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
│   └── AI_PROMPT_HISTORY.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 9. Installation and Setup

### Prerequisites

- Python 3.11 or later
- Git
- pip

### Step 1: Clone the repository

```bash
git clone https://github.com/Akshatabagewadi/workforce-retention-intelligence-system.git

cd workforce-retention-intelligence-system
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 5: Initialize the database

```bash
python -m generator.init_db
```

### Step 6: Generate master data

```bash
python -m generator.master_data
```

This creates the initial employee, role, and team records.

### Step 7: Generate employee histories

```bash
python -m generator.data_generator
```

This generates the employee history records, including tenure, engagement, workload, compensation, and promotion data.

### Step 8: Generate employee features

```bash
python -m analytics.feature_engineering
```

### Step 9: Train and evaluate the machine learning model

```bash
python -m analytics.evaluation
```

### Step 10: Export data

```bash
python -m generator.export_data
```

### Step 11: Validate the generated data

```bash
python -m validation.validate_data
```

### Step 12: Run automated tests

```bash
python -m pytest -v
```

### Step 13: Verify reproducibility

```bash
python -m generator.attrition_generator
```

This runs the in-memory reproducibility check. It generates attrition outcomes twice using the fixed seed and compares their SHA-256 checksums. It does not modify existing database records.

### Step 14: Launch the dashboard

```bash
python -m streamlit run dashboard/app.py
```

If the default port is occupied, use:

```bash
python -m streamlit run dashboard/app.py --server.port 8505
```

The dashboard will open in your browser.

**Important:** The database and trained model are excluded from GitHub. The data-generation commands should only be run against a fresh database. The reproducibility command checks deterministic outcome generation from existing employee history; it does not regenerate the complete dataset.

## 10. Generated Model Outputs

The model generates:

- `retention_model.joblib`
- `employee_risk_scores.csv`
- `feature_importance.csv`
- `confusion_matrix.csv`
- `model_metrics.json`

These files are saved in `data/processed/`.

## 11. Data Exports

The export script generates CSV and JSON files for all ten database tables, together with:

- `workforce_seed.sql`
- `source_manifest.json`
- `validation_summary.txt`

The source manifest contains file information and SHA-256 checksums to help verify exported file integrity.

The SQL seed file contains database records and assumes that the corresponding database schema has already been created.

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

The reproducibility test generates attrition outcomes twice using seed `20261022` and compares SHA-256 checksums.

## 13. Responsible AI and Limitations

This project uses entirely synthetic data and simulated attrition labels.

The model scores are not calibrated real-world probabilities. Risk categories and supporting signals are intended for demonstration and supportive HR review only.

The platform must not make automated hiring, firing, promotion, or other employment decisions.

Human review and contextual assessment are necessary before any intervention.

## 14. Future Enhancements

- Temporal model validation
- SHAP-based individual model explanations
- Human-review workflow
- Intervention outcome tracking
- Model calibration and fairness evaluation
- Automated reproducibility and integration tests
- Improved reporting and deployment


