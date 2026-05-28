"""
Reference table models for TCC v5.0 - Supabase Schema

These are the foundational tables that all other tables reference:
- Manufacturers: ABB, Eaton, Schneider Electric, etc. (450 rows)
- Trip Types: Trip unit models by manufacturer (1,276 rows)
- Trip Styles: Specific trip unit variants (1,368 rows)
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Manufacturer(Base):
    """
    Breaker and trip unit manufacturers

    Examples: ABB, Eaton, Schneider Electric, Siemens, GE, Square D, etc.
    Total records: 450 manufacturers
    """
    __tablename__ = 'tcc_manufacturers'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Data columns
    name = Column('mfr_name', String(100), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    trip_types = relationship("TripType", back_populates="manufacturer", cascade="all, delete-orphan")
    trip_styles = relationship("TripStyle", back_populates="manufacturer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Manufacturer(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return self.name


class TripType(Base):
    """
    Trip unit types per manufacturer

    Examples:
    - Eaton: Digitrip 1150, Digitrip 520, Digitrip RMS
    - Schneider: Micrologic 5.0, Micrologic 6.0
    - ABB: SACE PR122, PR123

    Total records: 1,276 trip types
    """
    __tablename__ = 'tcc_trip_types'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    manufacturer_id = Column(Integer, ForeignKey('tcc_manufacturers.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="trip_types")
    trip_styles = relationship("TripStyle", back_populates="trip_type", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('manufacturer_id', 'name', name='trip_types_mfg_id_name_key'),
        Index('idx_trip_types_manufacturer', 'manufacturer_id'),
        Index('idx_trip_types_name', 'name'),
    )

    def __repr__(self):
        return f"<TripType(id={self.id}, name='{self.name}', manufacturer_id={self.manufacturer_id})>"

    def __str__(self):
        return f"{self.name}"


class TripStyle(Base):
    """
    Trip unit styles - specific configurations of trip types

    Each trip type can have multiple styles with different ratings,
    settings, and curve characteristics.

    Examples:
    - Digitrip 1150 with different sensor configurations
    - Micrologic 5.0A vs 5.0P (different feature sets)

    Total records: 1,368 trip styles
    """
    __tablename__ = 'tcc_trip_styles'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    trip_type_id = Column(Integer, ForeignKey('tcc_trip_types.id', ondelete='CASCADE'), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('tcc_manufacturers.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    name = Column(String(100), nullable=False)
    notes = Column(Text)
    tcc_number = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    trip_type = relationship("TripType", back_populates="trip_styles")
    manufacturer = relationship("Manufacturer", back_populates="trip_styles")
    plugs = relationship('ETUPlug', back_populates='trip_style', cascade='all, delete-orphan')
    sensors = relationship('ETUSensor', back_populates='trip_style', cascade='all, delete-orphan')

    # Table constraints
    __table_args__ = (
        UniqueConstraint('trip_type_id', 'name', name='trip_styles_type_id_name_key'),
        Index('idx_trip_styles_type', 'trip_type_id'),
        Index('idx_trip_styles_manufacturer', 'manufacturer_id'),
        Index('idx_trip_styles_name', 'name'),
    )

    def __repr__(self):
        return f"<TripStyle(id={self.id}, name='{self.name}', trip_type_id={self.trip_type_id})>"

    def __str__(self):
        return f"{self.name}"
