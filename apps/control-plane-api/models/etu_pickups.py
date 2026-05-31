"""
ETU Pickups Models - Pickup Settings
====================================
Models for ETU pickup settings tables.

Tables:
- tcc.etu_ltpu_pickups: Long-Time Pickup settings (147,936 rows)
- tcc.etu_ltpu_multipliers: Long-Time Delay multipliers (242,220 rows)
- tcc.etu_stpu_pickups: Short-Time Pickup settings (80,127 rows)
- tcc.etu_inst_pickups: Instantaneous settings (67,155 rows)
- tcc.etu_gfpu_pickups: Ground Fault Pickup settings (29,336 rows)

Total: ~567K rows

These tables define the available pickup settings for each protection element.
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ETULTPUPickup(Base):
    """
    Long-Time Pickup Settings

    Defines available Long-Time (overload) pickup settings for each sensor.
    These are the current thresholds that trigger the LTD (Long-Time Delay) curve.

    Typical values: 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 (multipliers of sensor rating)

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_ltpu_pickups'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    value = Column(Numeric(10, 4), index=True,
                   comment='Pickup setting value')
    is_default = Column(Boolean, default=False,
                        comment='Is this the default setting?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Long-time pickup settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='ltpu_pickups')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.ltpu_pickup_id',
                              back_populates='ltpu_pickup')

    def __repr__(self):
        return f"<ETULTPUPickup(id={self.id}, sensor_id={self.sensor_id}, value={self.value})>"


class ETULTPUMultiplier(Base):
    """
    Long-Time Delay Multipliers (C values)

    Defines available multiplier/C values for Long-Time Delay curves.
    These adjust the time response of the thermal overload curve.

    Common values: 0.5, 1.0, 2.0, 4.0, 8.0, 16.0 (seconds at 6× pickup)

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'etu_ltpu_multipliers'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    c_value = Column(Numeric(10, 4),
                     comment='Multiplier C value')
    is_default = Column(Boolean, default=False,
                        comment='Is this the default multiplier?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Long-time multiplier/C values'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='ltpu_multipliers')

    def __repr__(self):
        return f"<ETULTPUMultiplier(id={self.id}, sensor_id={self.sensor_id}, C={self.c_value})>"


class ETUSTPUPickup(Base):
    """
    Short-Time Pickup Settings

    Defines available Short-Time (short circuit) pickup settings for each sensor.
    These are the current thresholds that trigger the STD (Short-Time Delay) curve.

    Typical values: 2×, 3×, 4×, 5×, 6×, 8×, 10×, 12× (multiples of sensor rating)
    Can also be "OFF" or specific amp values.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_stpu_pickups'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    label = Column(String(50),
                   comment='Setting description (e.g., "2x", "3x")')
    value = Column(Numeric(10, 4),
                   comment='Setting value')
    is_default = Column(Boolean, default=False,
                        comment='Is this the default setting?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Short-time pickup settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='stpu_pickups')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.stpu_pickup_id',
                              back_populates='stpu_pickup')

    def __repr__(self):
        return f"<ETUSTPUPickup(id={self.id}, sensor_id={self.sensor_id}, label={self.label})>"


class ETUInstPickup(Base):
    """
    Instantaneous Pickup Settings

    Defines available Instantaneous pickup settings for each sensor.
    These provide high-speed protection for severe short circuits.

    Typical values: 5×, 10×, 15×, 20×, 25×, 30×, 40× (multiples of sensor rating)
    Can also be "OFF", "MAIN" (maintenance mode), or specific amp values.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_inst_pickups'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    label = Column(String(50),
                   comment='Setting description')
    value = Column(Numeric(10, 4),
                   comment='Setting value')
    mode = Column(Integer,
                  comment='Mode (0=OFF, 1=Normal, 2=Maintenance)')
    is_default = Column(Boolean, default=False,
                        comment='Is this the default setting?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Instantaneous pickup settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='inst_pickups')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.inst_pickup_id',
                              back_populates='inst_pickup')

    def __repr__(self):
        return f"<ETUInstPickup(id={self.id}, sensor_id={self.sensor_id}, label={self.label})>"


class ETUGFPUPickup(Base):
    """
    Ground Fault Pickup Settings

    Defines available Ground Fault pickup settings for each sensor.
    These protect against ground fault conditions.

    Typical values: 0.2×, 0.3×, 0.4×, 0.5×, 0.6× (multiples of sensor rating)
    Can also be "OFF" or specific amp values like 300A, 600A, 1200A.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_gfpu_pickups'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    label = Column(String(50),
                   comment='Setting description')
    value = Column(Numeric(10, 4),
                   comment='Setting value')
    mode = Column(Integer,
                  comment='Mode (0=OFF, 1=Normal)')
    is_default = Column(Boolean, default=False,
                        comment='Is this the default setting?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Ground fault pickup settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='gfpu_pickups')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.gfpu_pickup_id',
                              back_populates='gfpu_pickup')

    def __repr__(self):
        return f"<ETUGFPUPickup(id={self.id}, sensor_id={self.sensor_id}, label={self.label})>"
