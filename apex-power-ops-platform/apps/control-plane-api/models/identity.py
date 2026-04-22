"""
Identity Domain — Minimal SQLAlchemy ORM Models
================================================
Packet: 2026-04-14-pm-schema-012e
Authority: infra/database/migrations/identity/002_identity_tables.sql

3 read-only models for the identity.* tables created by packet 012b:
  1. User      — identity.users
  2. Employee  — identity.employees
  3. Crew      — identity.crews

These models exist solely to support SQLAlchemy relationship() declarations
on the PM/work models (WorkPackage, Assignment, ExecutionIssue,
ProgressSnapshot) for the six identity foreign keys activated by packet 012d:

  work.work_packages.assigned_crew_id  -> identity.crews
  work.assignments.employee_id         -> identity.employees
  work.assignments.crew_id             -> identity.crews
  work.execution_issues.reported_by    -> identity.users
  work.execution_issues.assigned_to    -> identity.users
  work.progress_snapshots.approved_by  -> identity.users

Column names, types, nullability, and defaults match the validated DDL
exactly.  These models are read-only — no write-side logic, services,
or API endpoints are introduced.

Do not expand these models beyond the minimum needed for FK relationship
support.  Full identity-domain CRUD is a future packet scope.
"""

from sqlalchemy import (
    Column, Text, Boolean,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from .base import Base


# ---------------------------------------------------------------------------
# identity.users
# ---------------------------------------------------------------------------

class User(Base):
    """Platform actor for workflow actions (identity.users)."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        {"schema": "identity"},
    )

    user_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — identity-internal
    employees = relationship("Employee", back_populates="user")

    # Relationships — cross-domain (work → identity)
    reported_issues = relationship(
        "ExecutionIssue", back_populates="reporter",
        foreign_keys="ExecutionIssue.reported_by",
    )
    assigned_issues = relationship(
        "ExecutionIssue", back_populates="assignee",
        foreign_keys="ExecutionIssue.assigned_to",
    )
    approved_snapshots = relationship(
        "ProgressSnapshot", back_populates="approver",
        foreign_keys="ProgressSnapshot.approved_by",
    )


# ---------------------------------------------------------------------------
# identity.employees
# ---------------------------------------------------------------------------

class Employee(Base):
    """Field worker identity (identity.employees)."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_employee_code"),
        {"schema": "identity"},
    )

    employee_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.user_id"),
        nullable=True,
    )
    employee_code = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    job_title = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — identity-internal
    user = relationship("User", back_populates="employees")

    # Relationships — cross-domain (work → identity)
    assignments = relationship(
        "Assignment", back_populates="employee",
        foreign_keys="Assignment.employee_id",
    )


# ---------------------------------------------------------------------------
# identity.crews
# ---------------------------------------------------------------------------

class Crew(Base):
    """Named work crew (identity.crews)."""

    __tablename__ = "crews"
    __table_args__ = (
        UniqueConstraint("crew_code", name="uq_crews_crew_code"),
        {"schema": "identity"},
    )

    crew_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    crew_code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — cross-domain (work → identity)
    assigned_work_packages = relationship(
        "WorkPackage", back_populates="assigned_crew",
        foreign_keys="WorkPackage.assigned_crew_id",
    )
    assignments = relationship(
        "Assignment", back_populates="crew",
        foreign_keys="Assignment.crew_id",
    )


# ---------------------------------------------------------------------------
# Model registry — maps SQL table name to ORM class
# ---------------------------------------------------------------------------

IDENTITY_MODEL_REGISTRY = {
    "users": User,
    "employees": Employee,
    "crews": Crew,
}

assert len(IDENTITY_MODEL_REGISTRY) == 3, (
    f"Expected 3 identity models, got {len(IDENTITY_MODEL_REGISTRY)}"
)
