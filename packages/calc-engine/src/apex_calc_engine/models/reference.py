"""Reference table models required by the extracted calc-domain package."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Manufacturer(Base):
    __tablename__ = 'manufacturers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = {'schema': 'tcc'}

    trip_types = relationship('TripType', back_populates='manufacturer', cascade='all, delete-orphan')
    trip_styles = relationship('TripStyle', back_populates='manufacturer', cascade='all, delete-orphan')


class TripType(Base):
    __tablename__ = 'trip_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_id = Column(Integer, ForeignKey('tcc.manufacturers.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    manufacturer = relationship('Manufacturer', back_populates='trip_types')
    trip_styles = relationship('TripStyle', back_populates='trip_type', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('manufacturer_id', 'name', name='trip_types_mfg_id_name_key'),
        Index('idx_trip_types_manufacturer', 'manufacturer_id'),
        Index('idx_trip_types_name', 'name'),
        {'schema': 'tcc'},
    )


class TripStyle(Base):
    __tablename__ = 'trip_styles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_type_id = Column(Integer, ForeignKey('tcc.trip_types.id', ondelete='CASCADE'), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('tcc.manufacturers.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    notes = Column(Text)
    tcc_number = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    trip_type = relationship('TripType', back_populates='trip_styles')
    manufacturer = relationship('Manufacturer', back_populates='trip_styles')
    plugs = relationship('ETUPlug', back_populates='trip_style', cascade='all, delete-orphan')
    sensors = relationship('ETUSensor', back_populates='trip_style', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('trip_type_id', 'name', name='trip_styles_type_id_name_key'),
        Index('idx_trip_styles_type', 'trip_type_id'),
        Index('idx_trip_styles_manufacturer', 'manufacturer_id'),
        Index('idx_trip_styles_name', 'name'),
        {'schema': 'tcc'},
    )
