
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)

from database.db import Base


# ==========================================
# 1. ROLE TABLE
# ==========================================

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String(30), primary_key=True)
    role_name = Column(String(100), unique=True, nullable=False)
    job_level = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# ==========================================
# 2. TEAM TABLE
# ==========================================

class Team(Base):
    __tablename__ = "teams"

    team_id = Column(String(30), primary_key=True)
    team_name = Column(String(100), unique=True, nullable=False)
    department = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# ==========================================
# 3. EMPLOYEE TABLE
# ==========================================

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String(30), primary_key=True)

    role_id = Column(
        String(30),
        ForeignKey("roles.role_id"),
        nullable=False
    )

    team_id = Column(
        String(30),
        ForeignKey("teams.team_id"),
        nullable=False
    )

    hire_date = Column(Date, nullable=False)

    employment_status = Column(
        String(30),
        default="ACTIVE",
        nullable=False
    )

    location_code = Column(String(30), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "employment_status IN ('ACTIVE', 'INACTIVE', 'TERMINATED')",
            name="check_employment_status"
        ),
    )


# ==========================================
# 4. TENURE SNAPSHOT TABLE
# ==========================================

class TenureSnapshot(Base):
    __tablename__ = "tenure_snapshots"

    snapshot_id = Column(String(60), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    role_id = Column(
        String(30),
        ForeignKey("roles.role_id"),
        nullable=False
    )

    team_id = Column(
        String(30),
        ForeignKey("teams.team_id"),
        nullable=False
    )

    snapshot_date = Column(Date, nullable=False)
    tenure_months = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "snapshot_date",
            name="unique_employee_tenure_snapshot"
        ),
        CheckConstraint(
            "tenure_months >= 0",
            name="check_tenure_nonnegative"
        ),
    )


# ==========================================
# 5. ENGAGEMENT SURVEY TABLE
# ==========================================

class EngagementSurvey(Base):
    __tablename__ = "engagement_surveys"

    survey_id = Column(String(40), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    survey_date = Column(Date, nullable=False)

    engagement_score = Column(Integer, nullable=True)
    satisfaction_score = Column(Integer, nullable=True)
    career_growth_score = Column(Integer, nullable=True)

    survey_status = Column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "engagement_score IS NULL OR engagement_score BETWEEN 1 AND 5",
            name="check_engagement_score"
        ),
        CheckConstraint(
            "satisfaction_score IS NULL OR satisfaction_score BETWEEN 1 AND 5",
            name="check_satisfaction_score"
        ),
        CheckConstraint(
            "career_growth_score IS NULL OR career_growth_score BETWEEN 1 AND 5",
            name="check_career_growth_score"
        ),
        CheckConstraint(
            "survey_status IN ('COMPLETED', 'MISSING', 'PARTIAL')",
            name="check_survey_status"
        ),
    )


# ==========================================
# 6. WORKLOAD SNAPSHOT TABLE
# ==========================================

class WorkloadSnapshot(Base):
    __tablename__ = "workload_snapshots"

    workload_id = Column(String(60), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    snapshot_date = Column(Date, nullable=False)

    weekly_hours = Column(Float, nullable=False)
    overtime_hours = Column(Float, nullable=False)
    active_projects = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "snapshot_date",
            name="unique_employee_workload_snapshot"
        ),
        CheckConstraint(
            "weekly_hours >= 0",
            name="check_weekly_hours"
        ),
        CheckConstraint(
            "overtime_hours >= 0",
            name="check_overtime_hours"
        ),
        CheckConstraint(
            "active_projects >= 0",
            name="check_active_projects"
        ),
    )


# ==========================================
# 7. COMPENSATION BAND TABLE
# ==========================================

class CompensationBand(Base):
    __tablename__ = "compensation_bands"

    compensation_id = Column(String(60), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    band_name = Column(String(50), nullable=False)

    # Names match the existing SQLite database
    minimum_salary = Column(Float, nullable=False)
    maximum_salary = Column(Float, nullable=False)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "minimum_salary >= 0",
            name="check_min_salary"
        ),
        CheckConstraint(
            "maximum_salary >= minimum_salary",
            name="check_max_salary"
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="check_compensation_dates"
        ),
    )


# ==========================================
# 8. PROMOTION HISTORY TABLE
# ==========================================

class PromotionHistory(Base):
    __tablename__ = "promotion_history"

    promotion_id = Column(String(50), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    previous_role_id = Column(
        String(30),
        ForeignKey("roles.role_id"),
        nullable=False
    )

    new_role_id = Column(
        String(30),
        ForeignKey("roles.role_id"),
        nullable=False
    )

    promotion_date = Column(Date, nullable=False)
    promotion_type = Column(String(50), nullable=False)


# ==========================================
# 9. ATTRITION OUTCOME TABLE
# ==========================================

class AttritionOutcome(Base):
    __tablename__ = "attrition_outcomes"

    outcome_id = Column(String(50), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    observation_date = Column(Date, nullable=False)
    horizon_end_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)

    attrition_type = Column(String(30), nullable=False)

    voluntary_attrition = Column(
        Boolean,
        default=False,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "observation_date",
            name="unique_employee_outcome"
        ),
        CheckConstraint(
            "horizon_end_date >= observation_date",
            name="check_outcome_horizon"
        ),
        CheckConstraint(
            "termination_date IS NULL OR "
            "(termination_date > observation_date AND "
            "termination_date <= horizon_end_date)",
            name="check_termination_date"
        ),
        CheckConstraint(
            "attrition_type IN ('VOLUNTARY', 'INVOLUNTARY', 'NONE')",
            name="check_attrition_type"
        ),
    )


# ==========================================
# 10. INTERVENTION TABLE
# ==========================================

class Intervention(Base):
    __tablename__ = "interventions"

    intervention_id = Column(String(50), primary_key=True)

    employee_id = Column(
        String(30),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    intervention_date = Column(Date, nullable=False)

    intervention_type = Column(String(100), nullable=False)

    status = Column(
        String(30),
        default="PLANNED",
        nullable=False
    )

    reason = Column(String(500), nullable=True)

    human_reviewed = Column(
        Boolean,
        default=False,
        nullable=False
    )

    outcome_notes = Column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="check_intervention_status"
        ),
    )
