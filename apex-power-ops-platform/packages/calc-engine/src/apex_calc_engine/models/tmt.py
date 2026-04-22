"""
TMT (Thermal-Magnetic Trip) table models for TCC v5.0 - Supabase Schema

Thermal-Magnetic Trip units are electromechanical protection devices
that use:
- Thermal element: Bimetallic strip for overload protection (inverse time)
- Magnetic element: Instantaneous trip for short circuits

These tables store the time-current characteristics for TMT breakers.

WARNING: tcc_tmt_curves has 1.1M rows - largest table in database!
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class TMTFrame(Base):
    """
    TMT Frame Size definitions

    Each breaker style can have multiple frame sizes.
    Frame size determines the physical dimensions and continuous current rating.

    Note: breaker_style_id can reference ANY breaker style (ICCB, MCCB, or PCB)

    Total records: ~5,300 frame sizes
    """
    __tablename__ = 'tcc_tmt_frames'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key (polymorphic - can be ICCB, MCCB, or PCB style)
    breaker_style_id = Column(Integer, nullable=False)

    # Data columns
    breaker_class = Column(String(4))
    size = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    amps = relationship("TMTAmp", back_populates="frame", cascade="all, delete-orphan")
    curves = relationship("TMTCurve", back_populates="frame", cascade="all, delete-orphan")
    settings = relationship("TMTSetting", back_populates="frame", cascade="all, delete-orphan")
    thermal_adjs = relationship("TMTThermalAdj", back_populates="frame", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_tmt_frames_style', 'breaker_style_id'),
        Index('idx_tmt_frames_size', 'size'),
    )

    def __repr__(self):
        return f"<TMTFrame(id={self.id}, size='{self.size}')>"

    def __str__(self):
        return self.size or f"Frame {self.id}"


class TMTAmp(Base):
    """
    TMT Frame Amp Ratings

    Each frame size can have multiple amp rating configurations.
    This defines the available trip ratings for a given frame.

    Example: A 600A frame might be available in 400A, 500A, 600A ratings

    Total records: ~93,000 amp ratings
    """
    __tablename__ = 'tcc_tmt_amps'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    frame_id = Column(Integer, ForeignKey('tcc_tmt_frames.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    rating = Column(Numeric(10, 2), nullable=False)
    max_override = Column(Numeric(10, 2))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    frame = relationship("TMTFrame", back_populates="amps")

    # Indexes
    __table_args__ = (
        Index('idx_tmt_amps_frame', 'frame_id'),
        Index('idx_tmt_amps_rating', 'rating'),
    )

    def __repr__(self):
        return f"<TMTAmp(id={self.id}, rating={self.rating}A)>"

    def __str__(self):
        return f"{self.rating}A"


class TMTCurve(Base):
    """
    TMT Time-Current Curve Points

    ⚠️ WARNING: LARGEST TABLE IN DATABASE - 1.1M+ ROWS!

    Stores the actual time-current curve data points for TMT breakers.
    Each point represents a time (seconds) at a given current (amps).
    Multiple curves per frame size for different curve classes.

    Curve classes typically:
    - Class 0-2: Very inverse
    - Class 3-5: Inverse
    - Class 6-7: Extremely inverse

    Total records: 1,143,458 curve points (46% of all database rows!)
    """
    __tablename__ = 'tcc_tmt_curves'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    frame_id = Column(Integer, ForeignKey('tcc_tmt_frames.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    class_ = Column('class', Integer)
    time_sec = Column(Numeric(10, 4))
    current_amp = Column(Numeric(10, 2))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    frame = relationship("TMTFrame", back_populates="curves")

    # Indexes (CRITICAL for performance!)
    __table_args__ = (
        Index('idx_tmt_curves_frame', 'frame_id'),
        Index('idx_tmt_curves_class', 'class'),
        Index('idx_tmt_curves_frame_class', 'frame_id', 'class'),  # Composite for common queries
    )

    def __repr__(self):
        return f"<TMTCurve(id={self.id}, class={self.class_}, {self.current_amp}A @ {self.time_sec}s)>"

    def __str__(self):
        return f"Class {self.class_}: {self.current_amp}A @ {self.time_sec}s"


class TMTSetting(Base):
    """
    TMT Frame Setting Values

    Adjustable settings for TMT trip units.
    Includes setting value, description, and tolerance ranges.

    Common settings:
    - Thermal pickup (Long-Time)
    - Magnetic pickup (Instantaneous)
    - Time delay adjustments

    Total records: ~86,000 settings
    """
    __tablename__ = 'tcc_tmt_settings'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    frame_id = Column(Integer, ForeignKey('tcc_tmt_frames.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    value = Column(Numeric(10, 4))
    label = Column(String(100))
    tol_lo = Column(Numeric(10, 4))
    tol_hi = Column(Numeric(10, 4))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    frame = relationship("TMTFrame", back_populates="settings")

    # Indexes
    __table_args__ = (
        Index('idx_tmt_settings_frame', 'frame_id'),
    )

    def __repr__(self):
        label = f", {self.label}" if self.label else ""
        return f"<TMTSetting(id={self.id}, value={self.value}{label})>"

    def __str__(self):
        return f"{self.label}: {self.value}" if self.label else str(self.value)


class TMTThermalAdj(Base):
    """
    TMT Thermal Trip Adjustment

    Thermal adjustment factors modify the time-current curve for the thermal element.
    Used to compensate for:
    - Ambient temperature
    - Load factor
    - Coordination requirements

    Adjustments typically range from 0.7 to 1.0 (70% to 100% of nominal)

    Total records: ~4,200 thermal adjustments
    """
    __tablename__ = 'tcc_tmt_thermal_adj'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    frame_id = Column(Integer, ForeignKey('tcc_tmt_frames.id', ondelete='CASCADE'), nullable=False)

    # Data columns
    adjustment = Column(Numeric(7, 4))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    frame = relationship("TMTFrame", back_populates="thermal_adjs")

    # Indexes
    __table_args__ = (
        Index('idx_tmt_thermal_frame', 'frame_id'),
    )

    def __repr__(self):
        return f"<TMTThermalAdj(id={self.id}, adjustment={self.adjustment})>"

    def __str__(self):
        if self.adjustment:
            percent = float(self.adjustment) * 100
            return f"{percent:.1f}%"
        return "N/A"
