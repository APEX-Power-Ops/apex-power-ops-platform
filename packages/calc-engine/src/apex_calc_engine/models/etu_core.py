"""
ETU Core Models - Rating Plugs and Sensors
===========================================
Models for ETU (formerly SST - Solid State Trip) core configuration tables.

Tables:
- tcc.etu_plugs: Rating plugs per style (1,576 rows)
- tcc.etu_sensors: Master sensor configuration (66,156 rows)

These are the foundation for all ETU trip unit calculations.
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ETUPlug(Base):
    """
    ETU Rating Plugs

    Rating plugs define the available sensor ratings for each trip style.
    Common values: 800, 1000, 1200, 1600, 2000, 2500, 3200, 4000A

    Relationships:
    - Belongs to one trip_style (TripStyle)
    """

    __tablename__ = 'etu_plugs'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    trip_style_id = Column(Integer, ForeignKey('tcc.trip_styles.id', ondelete='CASCADE'),
                           nullable=False, index=True,
                           comment='FK to trip_styles - trip unit style')

    # Attributes
    value = Column(Integer, nullable=False, index=True,
                   comment='Plug rating value (800, 1200, 1600, etc.)')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Constraints
    __table_args__ = (
        UniqueConstraint('trip_style_id', 'value', name='uq_etu_plugs_style_value'),
        {'schema': 'tcc', 'comment': 'ETU rating plugs per style'}
    )

    # Relationships
    trip_style = relationship('TripStyle', back_populates='plugs')

    def __repr__(self):
        return f"<ETUPlug(id={self.id}, trip_style_id={self.trip_style_id}, value={self.value}A)>"


class ETUSensor(Base):
    """
    ETU Sensor Master Configuration

    Master configuration for each sensor rating. Contains calculation methods,
    tolerances, section names, and step sizes for all protection elements:
    - LTPU: Long-Time Pickup (overload)
    - LTD: Long-Time Delay
    - STPU: Short-Time Pickup (short circuit)
    - STD: Short-Time Delay
    - INST: Instantaneous (instantaneous trip)
    - GFPU: Ground Fault Pickup
    - GFD: Ground Fault Delay

    Each sensor can have 100+ related setting/curve records.

    Relationships:
    - Belongs to one trip_style (TripStyle)
    - Has many ltpu_pickups (ETULTPUPickup)
    - Has many ltpu_multipliers (ETULTPUMultiplier)
    - Has many stpu_pickups (ETUSTPUPickup)
    - Has many inst_pickups (ETUInstPickup)
    - Has many gfpu_pickups (ETUGFPUPickup)
    - Has many ltd_bands (ETULTDBand)
    - Has many std_bands (ETUSTDBand)
    - Has many gfd_bands (ETUGFDBand)
    - Has many std_equations (ETUSTDEquation)
    - Has many gfd_equations (ETUGFDEquation)
    - Has many inst_curves (ETUInstCurve)
    - Has many sensor_params (ETUSensorParam)
    - Has many ltd_params (ETULTDParam)
    - Has many stpu_overrides (ETUSTPUOverride)
    - Has many maintenance_records (ETUSensorMaint)
    - Has many test_plans (TestPlan)
    """

    __tablename__ = 'etu_sensors'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    trip_style_id = Column(Integer, ForeignKey('tcc.trip_styles.id', ondelete='CASCADE'),
                           nullable=False, index=True,
                           comment='FK to trip_styles - trip unit style')

    # Core Attributes
    rating = Column(Integer, nullable=False, index=True,
                    comment='Sensor rating (800, 1200, 1600, etc.)')
    description = Column(String(200),
                         comment='Sensor description')

    # --- LTPU (Long-Time Pickup) Configuration ---
    ltpu_name = Column(String(50),
                       comment='LTPU section name')
    ltpu_calc = Column(Integer, index=True,
                       comment='LTPU calculation method')
    ltpu_tol_hi = Column(Numeric(5, 2),
                         comment='LTPU high tolerance %')
    ltpu_tol_lo = Column(Numeric(5, 2),
                         comment='LTPU low tolerance %')
    ltpu_step = Column(Numeric(10, 4),
                       comment='LTPU setting step size')

    # --- LTD (Long-Time Delay) Configuration ---
    ltd_name = Column(String(50),
                      comment='LTD section name')

    # --- STPU (Short-Time Pickup) Configuration ---
    stpu_name = Column(String(50),
                       comment='STPU section name')
    stpu_calc = Column(Integer, index=True,
                       comment='STPU calculation method')
    stpu_tol_hi = Column(Numeric(5, 2),
                         comment='STPU high tolerance %')
    stpu_tol_lo = Column(Numeric(5, 2),
                         comment='STPU low tolerance %')
    stpu_step = Column(Numeric(10, 4),
                       comment='STPU setting step size')

    # --- INST (Instantaneous) Configuration ---
    inst_name = Column(String(50),
                       comment='INST section name')
    inst_calc = Column(Integer,
                       comment='INST calculation method')
    inst_tol_hi = Column(Numeric(5, 2),
                         comment='INST high tolerance %')
    inst_tol_lo = Column(Numeric(5, 2),
                         comment='INST low tolerance %')

    # --- GFPU (Ground Fault Pickup) Configuration ---
    gfpu_name = Column(String(50),
                       comment='GFPU section name')
    gfpu_calc = Column(Integer,
                       comment='GFPU calculation method')
    gfpu_tol_hi = Column(Numeric(10, 2),
                         comment='GFPU high tolerance %')
    gfpu_tol_lo = Column(Numeric(10, 2),
                         comment='GFPU low tolerance %')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Constraints
    __table_args__ = (
        UniqueConstraint('trip_style_id', 'rating', name='uq_etu_sensors_style_rating'),
        {'schema': 'tcc', 'comment': 'ETU sensor master configuration'}
    )

    # Relationships
    trip_style = relationship('TripStyle', back_populates='sensors')

    # Settings Relationships
    ltpu_pickups = relationship('ETULTPUPickup', back_populates='sensor',
                                cascade='all, delete-orphan')
    ltpu_multipliers = relationship('ETULTPUMultiplier', back_populates='sensor',
                                    cascade='all, delete-orphan')
    stpu_pickups = relationship('ETUSTPUPickup', back_populates='sensor',
                                cascade='all, delete-orphan')
    inst_pickups = relationship('ETUInstPickup', back_populates='sensor',
                                cascade='all, delete-orphan')
    gfpu_pickups = relationship('ETUGFPUPickup', back_populates='sensor',
                                cascade='all, delete-orphan')

    # Delay Band Relationships
    ltd_bands = relationship('ETULTDBand', back_populates='sensor',
                             cascade='all, delete-orphan')
    std_bands = relationship('ETUSTDBand', back_populates='sensor',
                             cascade='all, delete-orphan')
    gfd_bands = relationship('ETUGFDBand', back_populates='sensor',
                             cascade='all, delete-orphan')

    # Equation Relationships
    std_equations = relationship('ETUSTDEquation', back_populates='sensor',
                                 cascade='all, delete-orphan')
    gfd_equations = relationship('ETUGFDEquation', back_populates='sensor',
                                 cascade='all, delete-orphan')

    # Curve/Parameter Relationships
    inst_curves = relationship('ETUInstCurve', back_populates='sensor',
                               cascade='all, delete-orphan')
    sensor_params = relationship('ETUSensorParam', back_populates='sensor',
                                 cascade='all, delete-orphan')
    ltd_params = relationship('ETULTDParam', back_populates='sensor',
                              cascade='all, delete-orphan')
    stpu_overrides = relationship('ETUSTPUOverride', back_populates='sensor',
                                  cascade='all, delete-orphan')
    maintenance_records = relationship('ETUSensorMaint', back_populates='sensor',
                                       cascade='all, delete-orphan')

    # User Data Relationships
    test_plans = relationship('TestPlan', back_populates='sensor',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f"<ETUSensor(id={self.id}, trip_style_id={self.trip_style_id}, rating={self.rating}A)>"

    @property
    def has_ltpu(self):
        """Check if sensor has Long-Time Pickup protection"""
        return self.ltpu_name is not None

    @property
    def has_stpu(self):
        """Check if sensor has Short-Time Pickup protection"""
        return self.stpu_name is not None

    @property
    def has_inst(self):
        """Check if sensor has Instantaneous protection"""
        return self.inst_name is not None

    @property
    def has_gfpu(self):
        """Check if sensor has Ground Fault Pickup protection"""
        return self.gfpu_name is not None
