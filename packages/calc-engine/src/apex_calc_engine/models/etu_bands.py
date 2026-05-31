"""
ETU Delay Band Models - Time Delay Settings
==========================================
Models for ETU delay band tables containing time-current curve parameters.

Tables:
- tcc.etu_ltd_bands: Long-Time Delay bands (189,618 rows)
- tcc.etu_std_bands: Short-Time Delay bands (119,780 rows)
- tcc.etu_gfd_bands: Ground Fault Delay bands (60,783 rows)

Total: ~370K rows

These tables contain the time-current curve equations and parameters
that define how quickly the breaker trips at various current levels.
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ETULTDBand(Base):
    """
    Long-Time Delay Band Settings

    Defines the time-current characteristics for Long-Time (thermal overload) protection.
    Each delay band represents a different time response curve (e.g., I²t, I⁴t).

    Contains equation parameters (k, x, sgf) used to calculate trip time:
        Time = k / (I^x - 1)  where I = Current / Pickup

    Also includes fixed time points (i_open, t_open, i_clear, t_clear) for
    specific current values.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_ltd_bands'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    ordinal = Column(Integer,
                     comment='Display order')
    band = Column(String(20), index=True,
                  comment='Delay band code')
    band_label = Column(String(50),
                        comment='Display name for delay band')

    # Fixed Time Points
    open_time = Column(Numeric(10, 4),
                       comment='Open time/setting')
    clear_time = Column(Numeric(10, 4),
                        comment='Clear time/setting')
    i_open = Column(Numeric(10, 4),
                    comment='Open current')
    i_clear = Column(Numeric(10, 4),
                     comment='Clear current')
    t_open = Column(Numeric(10, 4),
                    comment='Open time')
    t_clear = Column(Numeric(10, 4),
                     comment='Clear time')

    # Equation Parameters
    i2x = Column(Numeric(10, 4),
                 comment='I²t reference')
    exp_x = Column(Numeric(10, 4),
                   comment='Exponent for time equation')
    const_k = Column(Numeric(10, 4),
                     comment='Time constant k')
    sgf = Column(Numeric(10, 4),
                 comment='Slope/SGF factor')
    low_pickup = Column(Numeric(10, 4),
                        comment='Low pickup threshold')
    const_k_hi = Column(Numeric(10, 4),
                        comment='High k value')

    # References
    curve_id = Column(Integer,
                      comment='Curve identifier')

    # Metadata
    is_default = Column(Boolean, default=False,
                        comment='Is this the default delay band?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Long-time delay band settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='ltd_bands')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.ltd_band_id',
                              back_populates='ltd_band')

    def __repr__(self):
        return f"<ETULTDBand(id={self.id}, sensor_id={self.sensor_id}, band={self.band})>"


class ETUSTDBand(Base):
    """
    Short-Time Delay Band Settings

    Defines the time-current characteristics for Short-Time (short circuit) protection.
    Can be I²t inverse, I⁴t inverse, or definite time.

    Contains equation parameters (k, x, sgf) used to calculate trip time:
        Time = k / (I^x - 1)  where I = Current / Pickup

    For definite time: Time = constant regardless of current (above pickup)

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_std_bands'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    ordinal = Column(Integer,
                     comment='Display order')
    band = Column(String(20), nullable=False, index=True,
                  comment='Delay band code')
    band_label = Column(String(50),
                        comment='Display name for delay band')

    # Fixed Time Points
    open_time = Column(Numeric(10, 4),
                       comment='Open time/setting')
    clear_time = Column(Numeric(10, 4),
                        comment='Clear time/setting')
    i_open = Column(Numeric(10, 4),
                    comment='Open current')
    i_clear = Column(Numeric(10, 4),
                     comment='Clear current')
    t_open = Column(Numeric(10, 4),
                    comment='Open time')
    t_clear = Column(Numeric(10, 4),
                     comment='Clear time')

    # Equation Parameters
    i2x = Column(Numeric(10, 4),
                 comment='I²t reference')
    exp_x = Column(Numeric(10, 4),
                   comment='Exponent for time equation')
    const_k = Column(Numeric(10, 4),
                     comment='Time constant k')
    sgf = Column(Numeric(10, 4),
                 comment='Slope/SGF factor')
    low_pickup = Column(Numeric(10, 4),
                        comment='Low pickup threshold')
    const_k_hi = Column(Numeric(10, 4),
                        comment='High k value')

    # Metadata
    is_default = Column(Boolean, default=False,
                        comment='Is this the default delay band?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Short-time delay band settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='std_bands')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.std_band_id',
                              back_populates='std_band')

    def __repr__(self):
        return f"<ETUSTDBand(id={self.id}, sensor_id={self.sensor_id}, band={self.band})>"


class ETUGFDBand(Base):
    """
    Ground Fault Delay Band Settings

    Defines the time-current characteristics for Ground Fault protection.
    Typically I²t inverse curves similar to STD but at lower current levels.

    Contains equation parameters (k, x, sgf) used to calculate trip time:
        Time = k / (I^x - 1)  where I = Current / Pickup

    Relationships:
    - Belongs to one sensor (ETUSensor)
    - Used by many test_plans (TestPlan)
    """

    __tablename__ = 'etu_gfd_bands'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc.etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    ordinal = Column(Integer,
                     comment='Display order')
    band = Column(String(20), nullable=False, index=True,
                  comment='Delay band code')
    band_label = Column(String(50),
                        comment='Display name for delay band')

    # Fixed Time Points
    open_time = Column(Numeric(10, 4),
                       comment='Open time/setting')
    clear_time = Column(Numeric(10, 4),
                        comment='Clear time/setting')
    i_open = Column(Numeric(10, 4),
                    comment='Open current')
    i_clear = Column(Numeric(10, 4),
                     comment='Clear current')
    t_open = Column(Numeric(10, 4),
                    comment='Open time')
    t_clear = Column(Numeric(10, 4),
                     comment='Clear time')

    # Equation Parameters
    i2x = Column(Numeric(10, 4),
                 comment='I²t reference')
    exp_x = Column(Numeric(10, 4),
                   comment='Exponent for time equation')
    const_k = Column(Numeric(10, 4),
                     comment='Time constant k')
    sgf = Column(Numeric(10, 4),
                 comment='Slope/SGF factor')
    low_pickup = Column(Numeric(10, 4),
                        comment='Low pickup threshold')
    const_k_hi = Column(Numeric(10, 4),
                        comment='High k value')

    # Metadata
    is_default = Column(Boolean, default=False,
                        comment='Is this the default delay band?')
    sort_order = Column(Integer,
                        comment='Display sort order')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'schema': 'tcc', 'comment': 'Ground fault delay band settings'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='gfd_bands')
    test_plans = relationship('TestPlan', foreign_keys='TestPlan.gfd_band_id',
                              back_populates='gfd_band')

    def __repr__(self):
        return f"<ETUGFDBand(id={self.id}, sensor_id={self.sensor_id}, band={self.band})>"
