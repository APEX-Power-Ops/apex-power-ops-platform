"""
ETU Curves & Parameters Models
==============================
Models for ETU curve points, indexed parameters, overrides, and maintenance.

Tables:
- tcc.etu_inst_curves: Instantaneous time-current curve points (94,873 rows)
- tcc.etu_sensor_params: Indexed sensor parameters (66,156 rows)
- tcc.etu_ltd_params: Section 2 (LTD) additional parameters (74,147 rows)
- tcc.etu_stpu_overrides: Short-time pickup overrides (3 rows)
- tcc.etu_sensor_maint: Sensor maintenance settings and persisted MAINT payload

Total: ~235K rows

These tables contain discrete curve points, indexed parameter arrays,
special override cases, and maintenance/alarm configurations.
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base


class ETUInstCurve(Base):
    """
    Instantaneous Time-Current Curve Points

    Discrete (current, time) data points that define the instantaneous
    trip characteristic curve. These are used to plot the curve and
    determine trip time at specific current levels.

    Multiple curve types/classes may exist per sensor (e.g., Class A, B, C).

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'etu_inst_curves'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    ordinal = Column(Integer,
                     comment='Sequence/sort order')
    class_ = Column('class', String(50), index=True,
                    comment='Curve class/type')
    current_amp = Column(Numeric(10, 2),
                         comment='Current in amps')
    time_sec = Column(Numeric(10, 4),
                      comment='Time in seconds')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Instantaneous time-current curve points'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='inst_curves')

    def __repr__(self):
        return f"<ETUInstCurve(id={self.id}, sensor_id={self.sensor_id}, I={self.current_amp}A, T={self.time_sec}s)>"


class ETUSensorParam(Base):
    """
    Sensor Parameters (Indexed Arrays)

    Indexed parameter arrays that store curve constants and configuration
    values for each sensor section:
    - Section 2: LTD (Long-Time Delay) parameters [0-15]
    - Section 3: STPU (Short-Time Pickup) parameters [0-15]
    - Section 4: INST (Instantaneous) parameters [0-15]

    Each section/index combination stores a specific parameter value used
    in curve calculations. For example:
    - Section 2, Index 0: LTD curve constant k
    - Section 2, Index 1: LTD exponent x
    - Section 3, Index 0: STPU I²t threshold

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'etu_sensor_params'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    section = Column(Integer, nullable=False, index=True,
                     comment='Section number (2=LTD, 3=STPU, 4=INST)')
    idx = Column(Integer, nullable=False, index=True,
                 comment='Parameter index 0-15')
    value = Column(Numeric(12, 6),
                   comment='Parameter value')
    curve_id = Column(Integer,
                      comment='Associated curve ID')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Indexed sensor parameters (curve constants)'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='sensor_params')

    def __repr__(self):
        return f"<ETUSensorParam(id={self.id}, sensor_id={self.sensor_id}, sec={self.section}, idx={self.idx})>"


class ETULTDParam(Base):
    """
    Section 2 (LTD) Additional Parameters

    Additional configuration parameters specific to Section 2 (Long-Time Delay).
    Contains curve names, setting methods, tolerances, slopes, and other
    LTD-specific settings not stored in the main sensor or parameter tables.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'etu_ltd_params'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    curve_id = Column(Integer, index=True,
                      comment='Curve identifier')
    curve_name = Column(String(50),
                        comment='Curve name')
    ordinal = Column(Integer,
                     comment='Display order')
    method = Column(Integer,
                    comment='Setting method')
    ltf = Column(Integer,
                 comment='LTF flag')
    tol_hi = Column(Numeric(5, 2),
                    comment='High tolerance %')
    tol_lo = Column(Numeric(5, 2),
                    comment='Low tolerance %')
    value = Column(Numeric(10, 4),
                   comment='Setting value')
    type_ = Column('type', Integer,
                   comment='Setting type')
    slope = Column(Numeric(10, 4),
                   comment='Slope value')
    step = Column(Numeric(10, 4),
                  comment='Step size')
    delay_priority = Column(Integer,
                            comment='Delay property')
    force_i2x_out = Column(Integer,
                           comment='Force I²t out flag')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Section 2 (LTD) additional parameters'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='ltd_params')

    def __repr__(self):
        return f"<ETULTDParam(id={self.id}, sensor_id={self.sensor_id}, curve={self.curve_name})>"


class ETUSTPUOverride(Base):
    """
    Short-Time Pickup Overrides

    Special override cases for STPU (Short-Time Pickup) calculations.
    Very few records (only 3) - handles manufacturer-specific edge cases
    where standard calculation methods don't apply.

    Override types include:
    - amps: Override pickup current calculation
    - open_time: Override opening time calculation
    - clear_time: Override clearing time calculation
    - tolerance_low: Override low tolerance
    - tolerance_high: Override high tolerance

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'etu_stpu_overrides'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       index=True,
                       comment='FK to etu_sensors')

    # Attributes
    type_ = Column('type', String(50),
                   comment='Override type (amps, open_time, clear_time, tolerance_low, tolerance_high)')
    value = Column(Numeric(10, 4),
                   comment='Override value')
    description = Column(String,
                         comment='Description of override reason/purpose')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Short-time pickup overrides'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='stpu_overrides')

    def __repr__(self):
        return f"<ETUSTPUOverride(id={self.id}, sensor_id={self.sensor_id}, type={self.type_})>"


class ETUSensorMaint(Base):
    """
    Sensor Maintenance and Alarm Settings

        This table is an active persisted MAINT branch surface.

        Current reviewed population uses a mixed storage pattern:
        - alarm and convenience columns exist on the relational model
        - the authoritative persisted MAINT execution payload for the current
            backend slice primarily lives in params_json
        - reviewed data shows MAINT INST and GF branches can be present even
            when maint_available is false, so capability must be inferred from
            the persisted payload rather than from that flag alone

        Reduction-factor columns remain sparsely or not populated in the
        reviewed dataset, so the current backend treats them as optional and
        emits explicit warnings when falling back to 1.0.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'etu_sensor_maint'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    alarm_type = Column(String(50), index=True,
                        comment='Type of alarm (overload, ground_fault, phase_loss, etc.)')
    alarm_threshold = Column(Numeric(10, 2),
                             comment='Alarm threshold value')
    alarm_enabled = Column(Boolean, default=False,
                           comment='Is alarm enabled?')

    # Maintenance Mode Configuration
    maint_available = Column(Boolean, default=False, index=True,
                             comment='Is maintenance mode available for this sensor?')
    maint_ltpu_reduction = Column(Numeric(5, 2),
                                  comment='LTPU reduction % in maintenance mode')
    maint_stpu_reduction = Column(Numeric(5, 2),
                                  comment='STPU reduction % in maintenance mode')
    maint_inst_reduction = Column(Numeric(5, 2),
                                  comment='INST reduction % in maintenance mode')

    # Flexible Storage for Additional Parameters
    params_json = Column(JSONB,
                         comment='Additional maintenance/INST/GF parameters as JSON')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Constraints
    __table_args__ = (
        UniqueConstraint('sensor_id', 'alarm_type', name='uq_etu_maint_sensor_alarm'),
        {'schema': 'tcc', 'comment': 'Sensor maintenance and alarm settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='maintenance_records')

    def __repr__(self):
        return f"<ETUSensorMaint(id={self.id}, sensor_id={self.sensor_id}, alarm={self.alarm_type})>"
