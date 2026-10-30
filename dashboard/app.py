import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import plotly.express as px

from database.db import SessionLocal
from database.models import (
    Employee,
    Role,
    Team,
    AttritionOutcome,
    EngagementSurvey,
    WorkloadSnapshot,
    Intervention,
)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Workforce Retention Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Workforce Retention Intelligence System")

st.caption(
    "Explainable AI-Powered Employee Engagement "
    "& Retention Analytics Platform"
)


# ==========================================
# LOAD DATABASE DATA
# ==========================================

@st.cache_data(ttl=60)
def load_data():

    db = SessionLocal()

    try:
        employees = pd.read_sql(
            db.query(Employee).statement, db.bind
        )

        outcomes = pd.read_sql(
            db.query(AttritionOutcome).statement, db.bind
        )

        roles = pd.read_sql(
            db.query(Role).statement, db.bind
        )

        teams = pd.read_sql(
            db.query(Team).statement, db.bind
        )

        surveys = pd.read_sql(
            db.query(EngagementSurvey).statement, db.bind
        )

        workloads = pd.read_sql(
            db.query(WorkloadSnapshot).statement, db.bind
        )

        interventions = pd.read_sql(
            db.query(Intervention).statement, db.bind
        )

        return (
            employees,
            outcomes,
            roles,
            teams,
            surveys,
            workloads,
            interventions,
        )

    finally:
        db.close()


try:
    (
        employees,
        outcomes,
        roles,
        teams,
        surveys,
        workloads,
        interventions,
    ) = load_data()

except Exception as error:
    st.error(f"Unable to load database data: {error}")
    st.stop()


if employees.empty or outcomes.empty:
    st.warning("Required employee or outcome data is unavailable.")
    st.stop()


# ==========================================
# PREPARE DATA
# ==========================================

employee_view = employees.merge(
    outcomes[
        ["employee_id", "voluntary_attrition", "termination_date"]
    ],
    on="employee_id",
    how="left"
)

employee_view = employee_view.merge(
    roles[["role_id", "role_name", "job_level"]],
    on="role_id",
    how="left"
)

employee_view = employee_view.merge(
    teams[["team_id", "team_name", "department"]],
    on="team_id",
    how="left"
)


# ==========================================
# LOAD AI EMPLOYEE RISK SCORES
# ==========================================

risk_scores_path = (
    ROOT_DIR
    / "data"
    / "processed"
    / "employee_risk_scores.csv"
)

expected_risk_columns = [
    "employee_id",
    "risk_score_pct",
    "risk_category",
    "explainable_signals",
    "signal_count",
    "recommended_support",
]

if risk_scores_path.exists():

    risk_scores = pd.read_csv(risk_scores_path)

    missing_risk_columns = [
        column
        for column in expected_risk_columns
        if column not in risk_scores.columns
    ]

    if missing_risk_columns:

        st.warning(
            "The employee risk-score file is missing expected columns: "
            + ", ".join(missing_risk_columns)
        )

        risk_scores = pd.DataFrame(
            columns=expected_risk_columns
        )

    else:

        risk_scores = risk_scores[
            expected_risk_columns
        ].copy()

        risk_scores = risk_scores.drop_duplicates(
            subset=["employee_id"]
        )

else:

    risk_scores = pd.DataFrame(
        columns=expected_risk_columns
    )

    st.warning(
        "AI risk scores are not available yet. "
        "Run `python -m analytics.evaluation` "
        "to generate them."
    )


# Merge risk scores with employee data.

if not risk_scores.empty:

    employee_view = employee_view.merge(
        risk_scores,
        on="employee_id",
        how="left",
        validate="one_to_one"
    )

else:

    for column in [
        "risk_score_pct",
        "risk_category",
        "explainable_signals",
        "signal_count",
        "recommended_support",
    ]:
        employee_view[column] = pd.NA


employee_view["Retention Status"] = employee_view[
    "voluntary_attrition"
].map({
    True: "Voluntary Attrition",
    False: "Retained"
})

employee_view["Retention Status"] = (
    employee_view["Retention Status"].fillna("Unknown")
)


total_employees = len(employees)

leavers = int(
    outcomes["voluntary_attrition"].fillna(False).sum()
)

retained = total_employees - leavers

attrition_rate = (
    leavers / total_employees * 100
    if total_employees else 0
)

retention_rate = 100 - attrition_rate


# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.header("Dashboard Filters")

departments = sorted(
    employee_view["department"].dropna().unique().tolist()
)

selected_departments = st.sidebar.multiselect(
    "Select Department",
    departments,
    default=departments
)

retention_options = [
    "All",
    "Retained",
    "Voluntary Attrition"
]

selected_status = st.sidebar.selectbox(
    "Retention Status",
    retention_options
)

filtered_data = employee_view[
    employee_view["department"].isin(selected_departments)
].copy()

if selected_status != "All":

    filtered_data = filtered_data[
        filtered_data["Retention Status"] == selected_status
    ]


# ==========================================
# 1. WORKFORCE OVERVIEW
# ==========================================

st.subheader("1. Workforce Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Employees",
    f"{total_employees:,}"
)

col2.metric(
    "Voluntary Leavers",
    f"{leavers:,}"
)

col3.metric(
    "Attrition Rate",
    f"{attrition_rate:.2f}%"
)

col4.metric(
    "Retention Rate",
    f"{retention_rate:.2f}%"
)

st.divider()


# ==========================================
# 2. RETENTION DISTRIBUTION
# ==========================================

st.subheader("2. Retention Distribution")

chart_data = pd.DataFrame({
    "Status": [
        "Retained",
        "Voluntary Attrition"
    ],
    "Employees": [
        retained,
        leavers
    ]
})

fig = px.pie(
    chart_data,
    names="Status",
    values="Employees",
    hole=0.45,
    title="Workforce Retention vs Attrition"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()


# ==========================================
# 3. DEPARTMENT ANALYSIS
# ==========================================

st.subheader("3. Department-wise Attrition")

department_data = employee_view.groupby(
    "department",
    dropna=False
).agg(
    Total_Employees=("employee_id", "count"),
    Voluntary_Leavers=("voluntary_attrition", "sum")
).reset_index()

department_data["Attrition Rate (%)"] = (
    department_data["Voluntary_Leavers"]
    / department_data["Total_Employees"] * 100
)

fig = px.bar(
    department_data,
    x="department",
    y="Attrition Rate (%)",
    color="department",
    title="Attrition Rate by Department",
    text_auto=".2f"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()


# ==========================================
# 4. ROLE ANALYSIS
# ==========================================

st.subheader("4. Role-wise Workforce Analysis")

role_data = employee_view.groupby(
    "role_name",
    dropna=False
).agg(
    Total_Employees=("employee_id", "count"),
    Voluntary_Leavers=("voluntary_attrition", "sum")
).reset_index()

fig = px.bar(
    role_data,
    x="role_name",
    y="Total_Employees",
    color="Voluntary_Leavers",
    title="Employee Distribution by Role",
    barmode="group"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()


# ==========================================
# 5. ENGAGEMENT ANALYSIS
# ==========================================

st.subheader("5. Employee Engagement Insights")

if not surveys.empty:

    completed_surveys = surveys[
        surveys["survey_status"] == "COMPLETED"
    ].copy()

    if not completed_surveys.empty:

        engagement_summary = completed_surveys[
            [
                "engagement_score",
                "satisfaction_score",
                "career_growth_score",
            ]
        ].mean().reset_index()

        engagement_summary.columns = [
            "Engagement Metric",
            "Average Score"
        ]

        fig = px.bar(
            engagement_summary,
            x="Engagement Metric",
            y="Average Score",
            title="Average Employee Survey Scores",
            range_y=[0, 5],
            text_auto=".2f"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            f"Completed survey records: "
            f"{len(completed_surveys):,}"
        )

    else:

        st.info("No completed surveys available.")

else:

    st.info("Survey data is unavailable.")

st.divider()


# ==========================================
# 6. WORKLOAD ANALYSIS
# ==========================================

st.subheader("6. Workload Insights")

if not workloads.empty:

    workload_summary = workloads.groupby(
        "employee_id"
    ).agg(
        Average_Weekly_Hours=("weekly_hours", "mean"),
        Average_Overtime=("overtime_hours", "mean")
    ).reset_index()

    col1, col2 = st.columns(2)

    col1.metric(
        "Average Weekly Hours",
        f"{workload_summary['Average_Weekly_Hours'].mean():.2f}"
    )

    col2.metric(
        "Average Overtime Hours",
        f"{workload_summary['Average_Overtime'].mean():.2f}"
    )

    fig = px.histogram(
        workload_summary,
        x="Average_Weekly_Hours",
        nbins=20,
        title="Employee Weekly Workload Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info("Workload data is unavailable.")

st.divider()


# ==========================================
# 7. AI-GENERATED EMPLOYEE RETENTION RISK
# ==========================================

st.subheader("7. AI-Generated Employee Retention Risk")

st.caption(
    "Scores are generated by the Random Forest model using synthetic, "
    "rule-generated outcomes. They are demonstration scores, not calibrated "
    "real-world probabilities or automated employment decisions. "
    "The listed signals are transparent rule-based indicators; they are "
    "not causal explanations of the model score."
)

if not risk_scores.empty:

    visible_employee_ids = filtered_data[
        "employee_id"
    ].unique()

    risk_view = risk_scores[
        risk_scores["employee_id"].isin(
            visible_employee_ids
        )
    ].copy()

    if not risk_view.empty:

        risk_view["risk_category"] = pd.Categorical(
            risk_view["risk_category"],
            categories=["HIGH", "MEDIUM", "LOW"],
            ordered=True
        )

        high_count = int(
            (risk_view["risk_category"] == "HIGH").sum()
        )

        medium_count = int(
            (risk_view["risk_category"] == "MEDIUM").sum()
        )

        low_count = int(
            (risk_view["risk_category"] == "LOW").sum()
        )

        average_score = risk_view[
            "risk_score_pct"
        ].mean()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "High Priority",
            f"{high_count:,}"
        )

        col2.metric(
            "Medium Priority",
            f"{medium_count:,}"
        )

        col3.metric(
            "Low Priority",
            f"{low_count:,}"
        )

        col4.metric(
            "Average Model Score",
            (
                f"{average_score:.2f}%"
                if pd.notna(average_score)
                else "N/A"
            )
        )

        # Risk distribution chart.

        category_chart = (
            risk_view["risk_category"]
            .value_counts()
            .reindex(
                ["LOW", "MEDIUM", "HIGH"],
                fill_value=0
            )
            .rename_axis("Risk Category")
            .reset_index(name="Employees")
        )

        fig = px.bar(
            category_chart,
            x="Risk Category",
            y="Employees",
            color="Risk Category",
            title="Employee Distribution by Model Risk Category",
            text_auto=True,
            category_orders={
                "Risk Category": [
                    "LOW",
                    "MEDIUM",
                    "HIGH"
                ]
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # Employee-level risk table.

        st.markdown("#### Employee-level risk scores")

        category_filter = st.multiselect(
            "Filter by model risk category",
            options=[
                "HIGH",
                "MEDIUM",
                "LOW"
            ],
            default=[
                "HIGH",
                "MEDIUM",
                "LOW"
            ],
            key="risk_category_filter"
        )

        displayed_risks = risk_view[
            risk_view["risk_category"].astype(str).isin(
                category_filter
            )
        ].copy()

        displayed_risks = displayed_risks.merge(
            employee_view[
                [
                    "employee_id",
                    "department",
                    "role_name"
                ]
            ].drop_duplicates("employee_id"),
            on="employee_id",
            how="left"
        )

        displayed_risks = displayed_risks.sort_values(
            "risk_score_pct",
            ascending=False
        )

        st.dataframe(
            displayed_risks[
                [
                    "employee_id",
                    "department",
                    "role_name",
                    "risk_score_pct",
                    "risk_category",
                    "explainable_signals",
                    "recommended_support",
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # Download AI risk report.

        st.download_button(
            "Download AI Employee Risk Report",
            displayed_risks.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="employee_ai_risk_report.csv",
            mime="text/csv"
        )

        # Individual employee lookup.

        st.markdown("#### Look up one employee")

        risk_employee_id = st.text_input(
            "Enter Employee ID to view their risk explanation",
            placeholder="Example: EMP-000001",
            key="risk_employee_search"
        )

        if risk_employee_id:

            employee_match = risk_view[
                risk_view["employee_id"].astype(str).str.contains(
                    risk_employee_id,
                    case=False,
                    na=False
                )
            ]

            if employee_match.empty:

                st.info(
                    "No matching employee found in the selected filters."
                )

            else:

                selected_employee = employee_match.iloc[0]

                detail_col1, detail_col2 = st.columns(2)

                detail_col1.metric(
                    "Model Score",
                    f"{selected_employee['risk_score_pct']:.2f}%"
                )

                detail_col2.metric(
                    "Risk Category",
                    str(selected_employee["risk_category"])
                )

                st.write(
                    "**Supporting signals:**",
                    selected_employee["explainable_signals"]
                )

                st.write(
                    "**Suggested supportive follow-up:**",
                    selected_employee["recommended_support"]
                )

                st.info(
                    "A human HR reviewer must assess the context before "
                    "any intervention. A model score alone should never "
                    "determine an employment decision."
                )

        st.caption(
            "Display bands: LOW = 0–30, MEDIUM = above 30–60, "
            "HIGH = above 60. These are demonstration thresholds, "
            "not validated decision cutoffs."
        )

    else:

        st.info(
            "No risk-score records match the current department and "
            "retention-status filters."
        )

else:

    st.info(
        "Run `python -m analytics.evaluation` to generate "
        "`data/processed/employee_risk_scores.csv`."
    )

st.divider()


# ==========================================
# 8. HR INTERVENTION TRACKING
# ==========================================

st.subheader("8. HR Intervention Tracking")

if not interventions.empty:

    active_interventions = interventions[
        interventions["status"].isin(
            [
                "PLANNED",
                "IN_PROGRESS",
                "COMPLETED"
            ]
        )
    ].copy()

    cancelled_count = int(
        (interventions["status"] == "CANCELLED").sum()
    )

    reviewed_count = int(
        active_interventions["human_reviewed"]
        .fillna(False).sum()
    )

    pending_review = int(
        (~active_interventions["human_reviewed"]
        .fillna(False)).sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Interventions",
        f"{len(interventions):,}"
    )

    col2.metric(
        "Active Interventions",
        f"{len(active_interventions):,}"
    )

    col3.metric(
        "Human Reviewed",
        f"{reviewed_count:,}"
    )

    col4.metric(
        "Pending Human Review",
        f"{pending_review:,}"
    )

    st.metric(
        "Cancelled Interventions",
        f"{cancelled_count:,}"
    )

    st.dataframe(
        active_interventions[
            [
                "intervention_id",
                "employee_id",
                "intervention_type",
                "status",
                "human_reviewed",
                "reason",
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No intervention records are available.")

st.divider()


# ==========================================
# 9. EMPLOYEE INFORMATION
# ==========================================

st.subheader("9. Employee Information")

search_id = st.text_input(
    "Search Employee ID",
    placeholder="Example: EMP-000001"
)

employee_table = filtered_data.copy()

if search_id:

    employee_table = employee_table[
        employee_table["employee_id"].astype(str).str.contains(
            search_id,
            case=False,
            na=False
        )
    ]

st.write(
    "Employees found:",
    len(employee_table)
)

st.dataframe(
    employee_table[
        [
            "employee_id",
            "role_name",
            "department",
            "hire_date",
            "Retention Status",
            "risk_score_pct",
            "risk_category",
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 10. DOWNLOAD REPORTS
# ==========================================

st.subheader("10. Download Reports")

csv_data = employee_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Employee Retention Report",
    data=csv_data,
    file_name="employee_retention_report.csv",
    mime="text/csv"
)


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Workforce Retention Intelligence System | "
    "Synthetic Demonstration Dataset | "
    "For supportive analytics only. "
    "No automated employment decisions."
)