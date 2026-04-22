"""User data models for persisted NETA plans and results.

These models are aligned to the live Supabase user-data tables rather than the
earlier local-only integer-key draft. The current live state remains in a
transition posture: UUID primary keys are active, plan snapshots are stored in
JSONB, and anonymous writes are still temporarily allowed only for the internal
demo path until auth-phase enforcement lands.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class TestPlan(Base):
    """Persisted NETA test plans backed by the live Supabase schema."""

    __tablename__ = 'tcc_test_plans'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment='Supabase-generated UUID primary key',
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('auth.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='Supabase auth ownership. Required for all steady-state plan writes.',
    )
    name = Column(String(200), nullable=True, index=True,
                  comment='Test plan name/identifier')
    project = Column(String(200),
                     comment='Project or facility name')
    equipment_tag = Column(String(100),
                           comment='Equipment tag/identifier')
    location = Column(String(200),
                      comment='Physical location of equipment')
    sensor_id = Column(Integer, ForeignKey('tcc_etu_sensors.id'),
                       nullable=True, index=True,
                       comment='FK to etu_sensors - sensor being tested')
    ltpu_pickup_id = Column(Integer, ForeignKey('tcc_etu_ltpu_pickups.id'),
                            comment='FK to etu_ltpu_pickups - selected LTPU pickup')
    ltd_band_id = Column(Integer, ForeignKey('tcc_etu_ltd_bands.id'),
                         comment='FK to etu_ltd_bands - selected LTD delay band')
    stpu_pickup_id = Column(Integer, ForeignKey('tcc_etu_stpu_pickups.id'),
                            comment='FK to etu_stpu_pickups - selected STPU pickup')
    std_band_id = Column(Integer, ForeignKey('tcc_etu_std_bands.id'),
                         comment='FK to etu_std_bands - selected STD delay band')
    inst_pickup_id = Column(Integer, ForeignKey('tcc_etu_inst_pickups.id'),
                            comment='FK to etu_inst_pickups - selected INST pickup')
    gfpu_pickup_id = Column(Integer, ForeignKey('tcc_etu_gfpu_pickups.id'),
                            comment='FK to etu_gfpu_pickups - selected GFPU pickup')
    gfd_band_id = Column(Integer, ForeignKey('tcc_etu_gfd_bands.id'),
                         comment='FK to etu_gfd_bands - selected GFD delay band')
    ltpu_test_amps = Column(Numeric(10, 2),
                            comment='LTPU test current (amperes)')
    ltpu_min_sec = Column(Numeric(10, 2),
                          comment='LTPU minimum acceptable trip time (seconds)')
    ltpu_max_sec = Column(Numeric(10, 2),
                          comment='LTPU maximum acceptable trip time (seconds)')
    std_test_amps = Column(Numeric(10, 2),
                           comment='STD test current (amperes)')
    std_min_sec = Column(Numeric(10, 2),
                         comment='STD minimum acceptable trip time (seconds)')
    std_max_sec = Column(Numeric(10, 2),
                         comment='STD maximum acceptable trip time (seconds)')
    inst_test_amps = Column(Numeric(10, 2),
                            comment='INST test current (amperes)')
    inst_min_sec = Column(Numeric(10, 2),
                          comment='INST minimum acceptable trip time (seconds)')
    inst_max_sec = Column(Numeric(10, 2),
                          comment='INST maximum acceptable trip time (seconds)')
    gfpu_test_amps = Column(Numeric(10, 2),
                            comment='GFPU test current (amperes)')
    gfpu_min_sec = Column(Numeric(10, 2),
                          comment='GFPU minimum acceptable trip time (seconds)')
    gfpu_max_sec = Column(Numeric(10, 2),
                          comment='GFPU maximum acceptable trip time (seconds)')
    settings_snapshot = Column(
        JSONB,
        comment='Structured settings snapshot used by the demo save/load path',
    )
    display_snapshot = Column(
        JSONB,
        comment='Display metadata and measurements used by the demo save/load path',
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        comment='Record creation timestamp')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                        comment='Record last update timestamp')

    __table_args__ = (
        {'comment': 'User-created test plans with authenticated Supabase ownership'}
    )

    sensor = relationship('ETUSensor', back_populates='test_plans')
    ltpu_pickup = relationship('ETULTPUPickup', foreign_keys=[ltpu_pickup_id],
                               back_populates='test_plans')
    ltd_band = relationship('ETULTDBand', foreign_keys=[ltd_band_id],
                            back_populates='test_plans')
    stpu_pickup = relationship('ETUSTPUPickup', foreign_keys=[stpu_pickup_id],
                               back_populates='test_plans')
    std_band = relationship('ETUSTDBand', foreign_keys=[std_band_id],
                            back_populates='test_plans')
    inst_pickup = relationship('ETUInstPickup', foreign_keys=[inst_pickup_id],
                               back_populates='test_plans')
    gfpu_pickup = relationship('ETUGFPUPickup', foreign_keys=[gfpu_pickup_id],
                               back_populates='test_plans')
    gfd_band = relationship('ETUGFDBand', foreign_keys=[gfd_band_id],
                            back_populates='test_plans')
    test_results = relationship('TestResult', back_populates='plan',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return f"<TestPlan(id={self.id}, name={self.name}, sensor_id={self.sensor_id})>"


class TestResult(Base):
    """Persisted NETA test results backed by the live Supabase schema."""

    __tablename__ = 'tcc_test_results'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment='Supabase-generated UUID primary key',
    )
    plan_id = Column(UUID(as_uuid=True), ForeignKey('tcc_test_plans.id', ondelete='CASCADE'),
                     nullable=False, index=True,
                     comment='FK to test_plans - parent test plan')
    test_type = Column(String(20), nullable=True, index=True,
                       comment='Test type (LTPU, STPU, INST, GFPU)')
    element = Column(String(20), nullable=False,
                     comment='Element tested (pickup, delay, etc.)')
    expected = Column(Numeric(12, 4),
                      comment='Expected/calculated value')
    actual = Column(Numeric(12, 4),
                    comment='Actual measured value')
    min_accept = Column(Numeric(12, 4),
                        comment='Minimum acceptable value')
    max_accept = Column(Numeric(12, 4),
                        comment='Maximum acceptable value')
    passed = Column(Boolean,
                    comment='Pass (true) or Fail (false)')
    tested_at = Column(DateTime(timezone=True), server_default=func.now(), index=True,
                       comment='Date/time test was performed')
    technician = Column(String(100),
                        comment='Name of technician who performed test')
    notes = Column(Text,
                   comment='Additional notes or observations')

    __table_args__ = (
        {'comment': 'Test results per plan'}
    )

    plan = relationship('TestPlan', back_populates='test_results')

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"<TestResult(id={self.id}, plan_id={self.plan_id}, type={self.test_type}, status={status})>"

    @property
    def is_within_tolerance(self):
        """Check if actual value is within acceptable limits"""
        if self.actual is None:
            return None
        if self.min_accept is not None and self.actual < self.min_accept:
            return False
        if self.max_accept is not None and self.actual > self.max_accept:
            return False
        return True

    @property
    def deviation_percent(self):
        """Calculate % deviation from expected value"""
        if self.expected is None or self.actual is None or self.expected == 0:
            return None
        return ((self.actual - self.expected) / self.expected) * 100
