"""
Breaker table models for TCC v5.0 - Supabase Schema

Circuit breaker models organized by type:
- ICCB: Insulated Case Circuit Breakers
- MCCB: Molded Case Circuit Breakers
- PCB: Power Circuit Breakers

Each breaker type has:
- Base table (breaker type info)
- Styles table (frame configurations)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


# ============================================================================
# BREAKER TYPE MODELS (3 tables)
# ============================================================================

class BrkICCB(Base):
    """
    Insulated Case Circuit Breakers (ICCB)

    Medium voltage breakers typically rated 600V to 5kV
    Used in commercial and industrial applications

    Total records: 312 breakers
    """
    __tablename__ = 'brk_iccb'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    manufacturer_id = Column(Integer, ForeignKey('tcc.manufacturers.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    name = Column(String(100), nullable=False)
    standard = Column(Numeric(3, 1))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    manufacturer = relationship("Manufacturer", backref="iccb_breakers")
    styles = relationship("BrkICCBStyle", back_populates="breaker", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_brk_iccb_manufacturer', 'manufacturer_id'),
        Index('idx_brk_iccb_name', 'name'),
        {'schema': 'tcc'},
    )

    def __repr__(self):
        return f"<BrkICCB(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return self.name


class BrkMCCB(Base):
    """
    Molded Case Circuit Breakers (MCCB)

    Low voltage breakers (120V to 690V)
    Most common type for commercial/industrial distribution

    Total records: 376 breakers
    """
    __tablename__ = 'brk_mccb'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    manufacturer_id = Column(Integer, ForeignKey('tcc.manufacturers.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    name = Column(String(100), nullable=False)
    standard = Column(Numeric(3, 1))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    manufacturer = relationship("Manufacturer", backref="mccb_breakers")
    styles = relationship("BrkMCCBStyle", back_populates="breaker", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_brk_mccb_manufacturer', 'manufacturer_id'),
        Index('idx_brk_mccb_name', 'name'),
        {'schema': 'tcc'},
    )

    def __repr__(self):
        return f"<BrkMCCB(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return self.name


class BrkPCB(Base):
    """
    Power Circuit Breakers (PCB / LVPCB)

    Low Voltage Power Circuit Breakers
    Large frame breakers for high current applications

    Total records: 138 breakers
    """
    __tablename__ = 'brk_pcb'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    manufacturer_id = Column(Integer, ForeignKey('tcc.manufacturers.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    name = Column(String(100), nullable=False)
    standard = Column(Numeric(3, 1))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    manufacturer = relationship("Manufacturer", backref="pcb_breakers")
    styles = relationship("BrkPCBStyle", back_populates="breaker", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_brk_pcb_manufacturer', 'manufacturer_id'),
        Index('idx_brk_pcb_name', 'name'),
        {'schema': 'tcc'},
    )

    def __repr__(self):
        return f"<BrkPCB(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return self.name


# ============================================================================
# BREAKER STYLE MODELS (3 tables)
# ============================================================================

class BrkICCBStyle(Base):
    """
    ICCB frame styles and configurations

    Each ICCB type can have multiple frame styles with different:
    - Voltage ratings
    - Interrupt ratings (kAIC)
    - Physical configurations

    Total records: 5,420 styles
    """
    __tablename__ = 'brk_iccb_styles'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    breaker_id = Column(Integer, ForeignKey('tcc.brk_iccb.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    frame = Column(String(100), nullable=False)
    voltage_id = Column(Integer)
    kaic_480v = Column(Numeric(10, 2))
    kaic_600v = Column(Numeric(10, 2))
    standard = Column(Numeric(3, 1))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    breaker = relationship("BrkICCB", back_populates="styles")

    # Indexes
    __table_args__ = (
        Index('idx_iccb_styles_breaker', 'breaker_id'),
        Index('idx_iccb_styles_frame', 'frame'),
        {'schema': 'tcc'},
    )

    def __repr__(self):
        return f"<BrkICCBStyle(id={self.id}, frame='{self.frame}')>"

    def __str__(self):
        return self.frame


class BrkMCCBStyle(Base):
    """
    MCCB frame styles and configurations

    Each MCCB type can have multiple frame styles with different:
    - Voltage ratings (240V, 480V, 600V)
    - Interrupt ratings (kAIC) at each voltage
    - Pole configurations (1P, 2P, 3P, 4P)
    - Interrupt classes

    Total records: 7,946 styles
    """
    __tablename__ = 'brk_mccb_styles'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    breaker_id = Column(Integer, ForeignKey('tcc.brk_mccb.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    frame = Column(String(100), nullable=False)
    voltage_id = Column(Integer)
    kaic_240v = Column(Numeric(10, 2))
    kaic_480v = Column(Numeric(10, 2))
    kaic_600v = Column(Numeric(10, 2))
    poles = Column(Integer)
    standard = Column(Numeric(3, 1))
    interrupt_class = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    breaker = relationship("BrkMCCB", back_populates="styles")

    # Indexes
    __table_args__ = (
        Index('idx_mccb_styles_breaker', 'breaker_id'),
        Index('idx_mccb_styles_frame', 'frame'),
        {'schema': 'tcc'},
    )

    def __repr__(self):
        return f"<BrkMCCBStyle(id={self.id}, frame='{self.frame}')>"

    def __str__(self):
        return self.frame


class BrkPCBStyle(Base):
    """
    PCB frame styles and configurations

    Each PCB type can have multiple frame styles with different:
    - Voltage ratings
    - Interrupt ratings (kAIC)
    - Frame configurations

    Total records: 856 styles
    """
    __tablename__ = 'brk_pcb_styles'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    breaker_id = Column(Integer, ForeignKey('tcc.brk_pcb.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    frame = Column(String(100), nullable=False)
    voltage_id = Column(Integer)
    kaic_480v = Column(Numeric(10, 2))
    kaic_600v = Column(Numeric(10, 2))
    standard = Column(Numeric(3, 1))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    breaker = relationship("BrkPCB", back_populates="styles")

    # Indexes
    __table_args__ = (
        Index('idx_pcb_styles_breaker', 'breaker_id'),
        Index('idx_pcb_styles_frame', 'frame'),
        {'schema': 'tcc'},
    )

    def __repr__(self):
        return f"<BrkPCBStyle(id={self.id}, frame='{self.frame}')>"

    def __str__(self):
        return self.frame
