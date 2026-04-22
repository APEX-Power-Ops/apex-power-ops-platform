"""Minimal user-data models needed to complete the ETU relationship graph."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class TestPlan(Base):
    __tablename__ = 'tcc_test_plans'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth.users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(200), nullable=True, index=True)
    project = Column(String(200))
    equipment_tag = Column(String(100))
    location = Column(String(200))
    sensor_id = Column(Integer, ForeignKey('tcc_etu_sensors.id'), nullable=True, index=True)
    ltpu_pickup_id = Column(Integer, ForeignKey('tcc_etu_ltpu_pickups.id'))
    ltd_band_id = Column(Integer, ForeignKey('tcc_etu_ltd_bands.id'))
    stpu_pickup_id = Column(Integer, ForeignKey('tcc_etu_stpu_pickups.id'))
    std_band_id = Column(Integer, ForeignKey('tcc_etu_std_bands.id'))
    inst_pickup_id = Column(Integer, ForeignKey('tcc_etu_inst_pickups.id'))
    gfpu_pickup_id = Column(Integer, ForeignKey('tcc_etu_gfpu_pickups.id'))
    gfd_band_id = Column(Integer, ForeignKey('tcc_etu_gfd_bands.id'))
    ltpu_test_amps = Column(Numeric(10, 2))
    ltpu_min_sec = Column(Numeric(10, 2))
    ltpu_max_sec = Column(Numeric(10, 2))
    std_test_amps = Column(Numeric(10, 2))
    std_min_sec = Column(Numeric(10, 2))
    std_max_sec = Column(Numeric(10, 2))
    inst_test_amps = Column(Numeric(10, 2))
    inst_min_sec = Column(Numeric(10, 2))
    inst_max_sec = Column(Numeric(10, 2))
    gfpu_test_amps = Column(Numeric(10, 2))
    gfpu_min_sec = Column(Numeric(10, 2))
    gfpu_max_sec = Column(Numeric(10, 2))
    settings_snapshot = Column(JSONB)
    display_snapshot = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sensor = relationship('ETUSensor', back_populates='test_plans')
    ltpu_pickup = relationship('ETULTPUPickup', foreign_keys=[ltpu_pickup_id], back_populates='test_plans')
    ltd_band = relationship('ETULTDBand', foreign_keys=[ltd_band_id], back_populates='test_plans')
    stpu_pickup = relationship('ETUSTPUPickup', foreign_keys=[stpu_pickup_id], back_populates='test_plans')
    std_band = relationship('ETUSTDBand', foreign_keys=[std_band_id], back_populates='test_plans')
    inst_pickup = relationship('ETUInstPickup', foreign_keys=[inst_pickup_id], back_populates='test_plans')
    gfpu_pickup = relationship('ETUGFPUPickup', foreign_keys=[gfpu_pickup_id], back_populates='test_plans')
    gfd_band = relationship('ETUGFDBand', foreign_keys=[gfd_band_id], back_populates='test_plans')
    test_results = relationship('TestResult', back_populates='plan', cascade='all, delete-orphan')


class TestResult(Base):
    __tablename__ = 'tcc_test_results'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    plan_id = Column(UUID(as_uuid=True), ForeignKey('tcc_test_plans.id', ondelete='CASCADE'), nullable=False, index=True)
    test_type = Column(String(20), nullable=True, index=True)
    element = Column(String(20), nullable=False)
    expected = Column(Numeric(12, 4))
    actual = Column(Numeric(12, 4))
    min_accept = Column(Numeric(12, 4))
    max_accept = Column(Numeric(12, 4))
    passed = Column(Boolean)
    tested_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    technician = Column(String(100))
    notes = Column(Text)

    plan = relationship('TestPlan', back_populates='test_results')