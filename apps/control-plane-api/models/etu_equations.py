"""
ETU Inverse Equation Models - IEEE Inverse Time Curves
=====================================================
Models for ETU inverse time equation tables.

Tables:
- tcc_etu_std_equations: STD inverse time equations (15,687 rows)
- tcc_etu_gfd_equations: GFD inverse time equations (15,483 rows)

Total: ~31K rows

These tables contain the coefficients for IEEE standard inverse time curves
(e.g., very inverse, extremely inverse, definite minimum time).

Each equation has 6 coefficients that define the curve shape:
    Time = (C1 / ((I^C2) - 1)) + C3 + C4*I + C5*I² + C6*I³

Where I = Current / Pickup
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class ETUSTDEquation(Base):
    """
    Short-Time Delay Inverse Time Equations

    IEEE standard inverse time curve equations for short-time protection.

    Standard curves include:
    - Moderately Inverse
    - Very Inverse
    - Extremely Inverse
    - Definite Minimum Time (DMT)
    - Long Time Inverse
    - Short Time Inverse

    Each equation has both frequency-dependent (FD) and frequency-independent (ID)
    versions, with separate coefficients for opening and clearing times.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'tcc_etu_std_equations'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc_etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    ordinal = Column(Integer,
                     comment='Display order')
    label = Column(String(50),
                   comment='Equation description')
    in_out = Column(Integer,
                    comment='In/Out flag')

    # --- Frequency-Dependent Opening Equation ---
    fd_open_eq = Column(Integer,
                        comment='FD open equation type')
    fd_open_1 = Column(Numeric(12, 6),
                       comment='FD open coefficient 1 (C1)')
    fd_open_2 = Column(Numeric(12, 6),
                       comment='FD open coefficient 2 (C2)')
    fd_open_3 = Column(Numeric(12, 6),
                       comment='FD open coefficient 3 (C3)')
    fd_open_4 = Column(Numeric(12, 6),
                       comment='FD open coefficient 4 (C4)')
    fd_open_5 = Column(Numeric(12, 6),
                       comment='FD open coefficient 5 (C5)')
    fd_open_6 = Column(Numeric(12, 6),
                       comment='FD open coefficient 6 (C6)')
    fd_open_i_calc = Column(Integer,
                            comment='FD open I calculation')

    # --- Frequency-Dependent Clearing Equation ---
    fd_clear_eq = Column(Integer,
                         comment='FD clear equation type')
    fd_clear_1 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 1')
    fd_clear_2 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 2')
    fd_clear_3 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 3')
    fd_clear_4 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 4')
    fd_clear_5 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 5')
    fd_clear_6 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 6')
    fd_clear_i_calc = Column(Integer,
                             comment='FD clear I calculation')

    # --- Frequency-Independent Opening Equation ---
    id_open_eq = Column(Integer,
                        comment='ID open equation type')
    id_open_1 = Column(Numeric(12, 6),
                       comment='ID open coefficient 1')
    id_open_2 = Column(Numeric(12, 6),
                       comment='ID open coefficient 2')
    id_open_3 = Column(Numeric(12, 6),
                       comment='ID open coefficient 3')
    id_open_4 = Column(Numeric(12, 6),
                       comment='ID open coefficient 4')
    id_open_5 = Column(Numeric(12, 6),
                       comment='ID open coefficient 5')
    id_open_6 = Column(Numeric(12, 6),
                       comment='ID open coefficient 6')
    id_open_i_calc = Column(Integer,
                            comment='ID open I calculation')

    # --- Frequency-Independent Clearing Equation ---
    id_clear_eq = Column(Integer,
                         comment='ID clear equation type')
    id_clear_1 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 1')
    id_clear_2 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 2')
    id_clear_3 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 3')
    id_clear_4 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 4')
    id_clear_5 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 5')
    id_clear_6 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 6')
    id_clear_i_calc = Column(Integer,
                             comment='ID clear I calculation')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'comment': 'STD inverse time equations (IEEE curves)'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='std_equations')

    def __repr__(self):
        return f"<ETUSTDEquation(id={self.id}, sensor_id={self.sensor_id}, label={self.label})>"


class ETUGFDEquation(Base):
    """
    Ground Fault Delay Inverse Time Equations

    IEEE standard inverse time curve equations for ground fault protection.
    Similar structure to STD equations but for ground fault curves.

    Standard curves include:
    - Moderately Inverse
    - Very Inverse
    - Extremely Inverse
    - Definite Minimum Time (DMT)

    Each equation has both frequency-dependent (FD) and frequency-independent (ID)
    versions, with separate coefficients for opening and clearing times.

    Relationships:
    - Belongs to one sensor (ETUSensor)
    """

    __tablename__ = 'tcc_etu_gfd_equations'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True,
                comment='Auto-increment primary key')

    # Foreign Keys
    sensor_id = Column(Integer, ForeignKey('tcc_etu_sensors.id', ondelete='CASCADE'),
                       nullable=False, index=True,
                       comment='FK to etu_sensors')

    # Attributes
    ordinal = Column(Integer,
                     comment='Display order')
    label = Column(String(50),
                   comment='Equation description')
    in_out = Column(Integer,
                    comment='In/Out flag')

    # --- Frequency-Dependent Opening Equation ---
    fd_open_eq = Column(Integer,
                        comment='FD open equation type')
    fd_open_1 = Column(Numeric(12, 6),
                       comment='FD open coefficient 1 (C1)')
    fd_open_2 = Column(Numeric(12, 6),
                       comment='FD open coefficient 2 (C2)')
    fd_open_3 = Column(Numeric(12, 6),
                       comment='FD open coefficient 3 (C3)')
    fd_open_4 = Column(Numeric(12, 6),
                       comment='FD open coefficient 4 (C4)')
    fd_open_5 = Column(Numeric(12, 6),
                       comment='FD open coefficient 5 (C5)')
    fd_open_6 = Column(Numeric(12, 6),
                       comment='FD open coefficient 6 (C6)')
    fd_open_i_calc = Column(Integer,
                            comment='FD open I calculation')

    # --- Frequency-Dependent Clearing Equation ---
    fd_clear_eq = Column(Integer,
                         comment='FD clear equation type')
    fd_clear_1 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 1')
    fd_clear_2 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 2')
    fd_clear_3 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 3')
    fd_clear_4 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 4')
    fd_clear_5 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 5')
    fd_clear_6 = Column(Numeric(12, 6),
                        comment='FD clear coefficient 6')
    fd_clear_i_calc = Column(Integer,
                             comment='FD clear I calculation')

    # --- Frequency-Independent Opening Equation ---
    id_open_eq = Column(Integer,
                        comment='ID open equation type')
    id_open_1 = Column(Numeric(12, 6),
                       comment='ID open coefficient 1')
    id_open_2 = Column(Numeric(12, 6),
                       comment='ID open coefficient 2')
    id_open_3 = Column(Numeric(12, 6),
                       comment='ID open coefficient 3')
    id_open_4 = Column(Numeric(12, 6),
                       comment='ID open coefficient 4')
    id_open_5 = Column(Numeric(12, 6),
                       comment='ID open coefficient 5')
    id_open_6 = Column(Numeric(12, 6),
                       comment='ID open coefficient 6')
    id_open_i_calc = Column(Integer,
                            comment='ID open I calculation')

    # --- Frequency-Independent Clearing Equation ---
    id_clear_eq = Column(Integer,
                         comment='ID clear equation type')
    id_clear_1 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 1')
    id_clear_2 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 2')
    id_clear_3 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 3')
    id_clear_4 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 4')
    id_clear_5 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 5')
    id_clear_6 = Column(Numeric(12, 6),
                        comment='ID clear coefficient 6')
    id_clear_i_calc = Column(Integer,
                             comment='ID clear I calculation')

    # Audit
    created_at = Column(DateTime, default=func.now(),
                        comment='Record creation timestamp')

    # Table Metadata
    __table_args__ = (
        {'comment': 'GFD inverse time equations (IEEE curves)'}
    )

    # Relationships
    sensor = relationship('ETUSensor', back_populates='gfd_equations')

    def __repr__(self):
        return f"<ETUGFDEquation(id={self.id}, sensor_id={self.sensor_id}, label={self.label})>"
