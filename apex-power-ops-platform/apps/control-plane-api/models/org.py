"""
Org Domain — Minimal SQLAlchemy ORM Models
===========================================
Packet: 2026-04-14-pm-schema-011e
Authority: infra/database/migrations/org/002_org_tables.sql

4 read-only models for the org.* tables created by packet 011b:
  1. Client          — org.clients
  2. Site            — org.sites
  3. BusinessUnit    — org.business_units
  4. Contract        — org.contracts

These models exist solely to support SQLAlchemy relationship() declarations
on the PM/work models (Project, WorkPackage) for the six org foreign keys
activated by packet 011d.

Column names, types, nullability, and defaults match the validated DDL
exactly.  These models are read-only — no write-side logic, services,
or API endpoints are introduced.

Do not expand these models beyond the minimum needed for FK relationship
support.  Full org-domain CRUD is a future packet scope.
"""

from sqlalchemy import (
    Column, String, Text, Boolean,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from .base import Base


# ---------------------------------------------------------------------------
# org.clients
# ---------------------------------------------------------------------------

class Client(Base):
    """Customer entity (org.clients)."""

    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("client_code", name="uq_clients_client_code"),
        {"schema": "org"},
    )

    client_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    client_code = Column(Text, nullable=False)
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

    # Relationships — org-internal
    sites = relationship("Site", back_populates="client")
    contracts = relationship("Contract", back_populates="client")

    # Relationships — cross-domain (work → org)
    projects = relationship(
        "Project", back_populates="client",
        foreign_keys="Project.client_id",
    )
    work_packages = relationship(
        "WorkPackage", back_populates="client",
        foreign_keys="WorkPackage.client_id",
    )


# ---------------------------------------------------------------------------
# org.sites
# ---------------------------------------------------------------------------

class Site(Base):
    """Physical work location (org.sites)."""

    __tablename__ = "sites"
    __table_args__ = (
        UniqueConstraint("client_id", "site_code", name="uq_sites_client_code"),
        {"schema": "org"},
    )

    site_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.clients.client_id"),
        nullable=False,
    )
    site_code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    address_line_1 = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state_province = Column(Text, nullable=True)
    postal_code = Column(Text, nullable=True)
    country = Column(Text, nullable=True, server_default=text("'US'"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — org-internal
    client = relationship("Client", back_populates="sites")

    # Relationships — cross-domain (work → org)
    projects = relationship(
        "Project", back_populates="site",
        foreign_keys="Project.site_id",
    )
    work_packages = relationship(
        "WorkPackage", back_populates="site",
        foreign_keys="WorkPackage.site_id",
    )


# ---------------------------------------------------------------------------
# org.business_units
# ---------------------------------------------------------------------------

class BusinessUnit(Base):
    """Internal organizational grouping (org.business_units)."""

    __tablename__ = "business_units"
    __table_args__ = (
        UniqueConstraint("code", name="uq_business_units_code"),
        {"schema": "org"},
    )

    business_unit_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code = Column(Text, nullable=False)
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

    # Relationships — cross-domain (work → org)
    projects = relationship(
        "Project", back_populates="business_unit",
        foreign_keys="Project.business_unit_id",
    )


# ---------------------------------------------------------------------------
# org.contracts
# ---------------------------------------------------------------------------

class Contract(Base):
    """Commercial agreement for work (org.contracts)."""

    __tablename__ = "contracts"
    __table_args__ = (
        UniqueConstraint("contract_code", name="uq_contracts_contract_code"),
        {"schema": "org"},
    )

    contract_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.clients.client_id"),
        nullable=False,
    )
    contract_code = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — org-internal
    client = relationship("Client", back_populates="contracts")

    # Relationships — cross-domain (work → org)
    projects = relationship(
        "Project", back_populates="contract",
        foreign_keys="Project.contract_id",
    )


# ---------------------------------------------------------------------------
# Model registry — maps SQL table name to ORM class
# ---------------------------------------------------------------------------

ORG_MODEL_REGISTRY = {
    "clients": Client,
    "sites": Site,
    "business_units": BusinessUnit,
    "contracts": Contract,
}

assert len(ORG_MODEL_REGISTRY) == 4, (
    f"Expected 4 org models, got {len(ORG_MODEL_REGISTRY)}"
)
