"""Relay ORM models for the shared calc-domain package."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class RelayTDSection(Base):
    __tablename__ = 'tcc_relay_td_sections'
    __table_args__ = {'schema': 'work'}

    relay_td_section_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_device_id = Column(UUID(as_uuid=True), nullable=False)
    relay_device_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    section_name = Column(Text, nullable=False)
    model_code = Column(Integer, nullable=False)
    type_code = Column(Integer, nullable=False)
    allow_trip_lt_st_delay = Column(Boolean, nullable=False, default=False)
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelayTDSection')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    iec_curves = relationship('RelayCurveIEC', back_populates='td_section')
    swz_curves = relationship('RelayCurveSWZ', back_populates='td_section')
    bsl_curves = relationship('RelayCurveBSL', back_populates='td_section')
    meq_curves = relationship('RelayCurveMEQ', back_populates='td_section')
    pcd_curves = relationship('RelayCurvePCD', back_populates='td_section')
    tcp_curves = relationship('RelayCurveTCP', back_populates='td_section')
    lrm_curves = relationship('RelayCurveLRM', back_populates='td_section')
    rxd_curves = relationship('RelayCurveRXD', back_populates='td_section')
    egc_curves = relationship('RelayCurveEGC', back_populates='td_section')


class RelayCurveIEC(Base):
    __tablename__ = 'tcc_relay_curves_iec'
    __table_args__ = {'schema': 'work'}

    relay_curve_iec_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2IEC')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='iec_curves')
    rows = relationship('RelayCurveRowIEC', back_populates='parent', order_by='RelayCurveRowIEC.ordinal')


class RelayCurveSWZ(Base):
    __tablename__ = 'tcc_relay_curves_swz'
    __table_args__ = {'schema': 'work'}

    relay_curve_swz_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2SWZ')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='swz_curves')
    rows = relationship('RelayCurveRowSWZ', back_populates='parent', order_by='RelayCurveRowSWZ.ordinal')


class RelayCurveBSL(Base):
    __tablename__ = 'tcc_relay_curves_bsl'
    __table_args__ = {'schema': 'work'}

    relay_curve_bsl_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2BSL')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='bsl_curves')
    rows = relationship('RelayCurveRowBSL', back_populates='parent', order_by='RelayCurveRowBSL.ordinal')


class RelayCurveMEQ(Base):
    __tablename__ = 'tcc_relay_curves_meq'
    __table_args__ = {'schema': 'work'}

    relay_curve_meq_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2MEQ')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='meq_curves')
    rows = relationship('RelayCurveRowMEQ', back_populates='parent', order_by='RelayCurveRowMEQ.ordinal')


class RelayCurvePCD(Base):
    __tablename__ = 'tcc_relay_curves_pcd'
    __table_args__ = {'schema': 'work'}

    relay_curve_pcd_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2PCD')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='pcd_curves')
    rows = relationship('RelayCurveRowPCD', back_populates='parent', order_by='RelayCurveRowPCD.ordinal')


class RelayCurveLRM(Base):
    __tablename__ = 'tcc_relay_curves_lrm'
    __table_args__ = {'schema': 'work'}

    relay_curve_lrm_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    lr_unit_code = Column(Integer, nullable=False)
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2LRM')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='lrm_curves')


class RelayCurveRXD(Base):
    __tablename__ = 'tcc_relay_curves_rxd'
    __table_args__ = {'schema': 'work'}

    relay_curve_rxd_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2RXD')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='rxd_curves')


class RelayCurveEGC(Base):
    __tablename__ = 'tcc_relay_curves_egc'
    __table_args__ = {'schema': 'work'}

    relay_curve_egc_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    min_pickup = Column(Numeric(20, 6))
    max_pickup = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2EGC')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='egc_curves')


class RelayCurveTCP(Base):
    __tablename__ = 'tcc_relay_curves_tcp'
    __table_args__ = {'schema': 'work'}

    relay_curve_tcp_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_td_section_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_td_sections.relay_td_section_id'), nullable=False)
    relay_td_section_source_id = Column(Integer, nullable=False)
    source_row_id = Column(Integer, nullable=False, unique=True)
    curve_name = Column(Text, nullable=False)
    tcc_number = Column(Text)
    ordinal = Column(Integer, nullable=False)
    is_discrete = Column(Boolean, nullable=False, default=False)
    step_size = Column(Numeric(20, 6))
    horizontal_amps_code = Column(Integer)
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2TCP')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    td_section = relationship('RelayTDSection', back_populates='tcp_curves')
    points = relationship('RelayCurvePointTCP', back_populates='parent', order_by='(RelayCurvePointTCP.source_ordinal, RelayCurvePointTCP.current_index)')


class RelayCurveRowIEC(Base):
    __tablename__ = 'tcc_relay_curve_rows_iec'
    __table_args__ = {'schema': 'work'}

    relay_curve_row_iec_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_curve_iec_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_curves_iec.relay_curve_iec_id'), nullable=False)
    relay_curve_iec_source_id = Column(Integer, nullable=False)
    curve_name = Column(Text, nullable=False)
    ordinal = Column(Integer, nullable=False)
    v_k = Column(Numeric(20, 6))
    v_e = Column(Numeric(20, 6))
    dt_after = Column(Numeric(20, 6))
    dt_min_time = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2IECCurves')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship('RelayCurveIEC', back_populates='rows')


class RelayCurveRowSWZ(Base):
    __tablename__ = 'tcc_relay_curve_rows_swz'
    __table_args__ = {'schema': 'work'}

    relay_curve_row_swz_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_curve_swz_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_curves_swz.relay_curve_swz_id'), nullable=False)
    relay_curve_swz_source_id = Column(Integer, nullable=False)
    curve_name = Column(Text, nullable=False)
    ordinal = Column(Integer, nullable=False)
    v_a = Column(Numeric(20, 6))
    v_b = Column(Numeric(20, 6))
    v_e = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2SWZCurves')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship('RelayCurveSWZ', back_populates='rows')


class RelayCurveRowBSL(Base):
    __tablename__ = 'tcc_relay_curve_rows_bsl'
    __table_args__ = {'schema': 'work'}

    relay_curve_row_bsl_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_curve_bsl_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_curves_bsl.relay_curve_bsl_id'), nullable=False)
    relay_curve_bsl_source_id = Column(Integer, nullable=False)
    curve_name = Column(Text, nullable=False)
    ordinal = Column(Integer, nullable=False)
    v_a = Column(Numeric(20, 6))
    v_b = Column(Numeric(20, 6))
    v_c = Column(Numeric(20, 6))
    v_d = Column(Numeric(20, 6))
    v_n = Column(Numeric(20, 6))
    v_k = Column(Numeric(20, 6))
    v_r = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2BSLCurves')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship('RelayCurveBSL', back_populates='rows')


class RelayCurveRowMEQ(Base):
    __tablename__ = 'tcc_relay_curve_rows_meq'
    __table_args__ = {'schema': 'work'}

    relay_curve_row_meq_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_curve_meq_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_curves_meq.relay_curve_meq_id'), nullable=False)
    relay_curve_meq_source_id = Column(Integer, nullable=False)
    curve_name = Column(Text, nullable=False)
    ordinal = Column(Integer, nullable=False)
    v_a = Column(Numeric(20, 6))
    v_b = Column(Numeric(20, 6))
    v_c = Column(Numeric(20, 6))
    v_d = Column(Numeric(20, 6))
    v_e = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2MEQCurves')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship('RelayCurveMEQ', back_populates='rows')


class RelayCurveRowPCD(Base):
    __tablename__ = 'tcc_relay_curve_rows_pcd'
    __table_args__ = {'schema': 'work'}

    relay_curve_row_pcd_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_curve_pcd_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_curves_pcd.relay_curve_pcd_id'), nullable=False)
    relay_curve_pcd_source_id = Column(Integer, nullable=False)
    curve_name = Column(Text, nullable=False)
    ordinal = Column(Integer, nullable=False)
    v_a = Column(Numeric(20, 6))
    v_b = Column(Numeric(20, 6))
    v_c = Column(Numeric(20, 6))
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2PCDCurves')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship('RelayCurvePCD', back_populates='rows')


class RelayCurvePointTCP(Base):
    __tablename__ = 'tcc_relay_curve_points_tcp'
    __table_args__ = {'schema': 'work'}

    relay_curve_point_tcp_id = Column(UUID(as_uuid=True), primary_key=True)
    relay_curve_tcp_id = Column(UUID(as_uuid=True), ForeignKey('work.tcc_relay_curves_tcp.relay_curve_tcp_id'), nullable=False)
    relay_curve_tcp_source_id = Column(Integer, nullable=False)
    time_dial = Column(Numeric(20, 6), nullable=False)
    td_desc = Column(Text)
    current_index = Column(Integer, nullable=False)
    current_value = Column(Numeric(20, 6), nullable=False)
    trip_time_seconds = Column(Numeric(20, 6), nullable=False)
    source_time_dial = Column(Numeric(20, 6), nullable=False)
    source_ordinal = Column(Integer, nullable=False)
    source_current_index = Column(Integer, nullable=False)
    source_snapshot_id = Column(Text)
    source_table_name = Column(Text, nullable=False, default='RelaySec2TCPCurves')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship('RelayCurveTCP', back_populates='points')