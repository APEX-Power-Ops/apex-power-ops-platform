#!/usr/bin/env python3
"""
TCC v5 Data Transfer Script
Exports from local PostgreSQL and imports into Supabase with column renaming.

Usage:
    python 002_data_transfer.py                    # Full transfer
    python 002_data_transfer.py --dry-run          # Preview only
    python 002_data_transfer.py --dry-run --verbose  # Detailed preview

Connection Details:
    Source: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL
    Target: DATABASE_URL
"""

import sys
import time
import json
import argparse
import os
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def describe_connection_target(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "unknown-host"
    port = parsed.port
    database = parsed.path.lstrip("/") or "postgres"
    if port:
        return f"{host}:{port}/{database}"
    return f"{host}/{database}"


# ============================================================================
# TABLE CONFIGURATION
# ============================================================================

# Column mapping: {old_name: new_name}
# Columns not in the dict keep their original name
TABLE_CONFIGS = {
    # Reference Tables
    "manufacturers": {
        "table": "tcc_manufacturers",
        "columns": {"mfg_id": "id", "mfg_name": "name"},
    },
    "trip_types": {
        "table": "tcc_trip_types",
        "columns": {"type_id": "id", "mfg_id": "manufacturer_id", "type_name": "name"},
    },
    "trip_styles": {
        "table": "tcc_trip_styles",
        "columns": {
            "style_id": "id",
            "type_id": "trip_type_id",
            "mfg_id": "manufacturer_id",
            "style_name": "name",
        },
    },
    # Breaker Tables
    "breaker_iccb": {
        "table": "tcc_brk_iccb",
        "columns": {
            "iccb_id": "id",
            "mfg_id": "manufacturer_id",
            "iccb_type": "name",
            "standard_type": "standard",
        },
    },
    "breaker_iccb_styles": {
        "table": "tcc_brk_iccb_styles",
        "columns": {
            "style_id": "id",
            "iccb_id": "breaker_id",
            "frame_name": "frame",
            "voltage_id": "voltage_id",
            "kaic_480v": "kaic_480v",
            "kaic_600v": "kaic_600v",
            "standard_type": "standard",
            "notes": "notes",
        },
    },
    "breaker_mccb": {
        "table": "tcc_brk_mccb",
        "columns": {
            "mccb_id": "id",
            "mfg_id": "manufacturer_id",
            "mccb_type": "name",
            "standard_type": "standard",
        },
    },
    "breaker_mccb_styles": {
        "table": "tcc_brk_mccb_styles",
        "columns": {
            "style_id": "id",
            "mccb_id": "breaker_id",
            "frame_name": "frame",
            "voltage_id": "voltage_id",
            "kaic_240v": "kaic_240v",
            "kaic_480v": "kaic_480v",
            "kaic_600v": "kaic_600v",
            "poles": "poles",
            "standard_type": "standard",
            "interrupt_class": "interrupt_class",
            "notes": "notes",
        },
    },
    "breaker_pcb": {
        "table": "tcc_brk_pcb",
        "columns": {
            "pcb_id": "id",
            "mfg_id": "manufacturer_id",
            "pcb_type": "name",
            "standard_type": "standard",
        },
    },
    "breaker_pcb_styles": {
        "table": "tcc_brk_pcb_styles",
        "columns": {
            "style_id": "id",
            "pcb_id": "breaker_id",
            "frame_name": "frame",
            "voltage_id": "voltage_id",
            "kaic_480v": "kaic_480v",
            "kaic_600v": "kaic_600v",
            "standard_type": "standard",
            "notes": "notes",
        },
    },
    # TMT Tables
    "breaker_tmt_frame_sizes": {
        "table": "tcc_tmt_frames",
        "columns": {
            "frame_size_id": "id",
            "style_id": "breaker_style_id",
            "frame_size": "size",
        },
        "special": "breaker_class_backfill",
    },
    "breaker_tmt_frame_amps": {
        "table": "tcc_tmt_amps",
        "columns": {
            "frame_amp_id": "id",
            "frame_size_id": "frame_id",
            "amp_rating": "rating",
        },
    },
    "breaker_tmt_frame_curves": {
        "table": "tcc_tmt_curves",
        "columns": {
            "curve_id": "id",
            "frame_size_id": "frame_id",
            "curve_class": "class",
            "time_seconds": "time_sec",
            "current_amps": "current_amp",
        },
    },
    "breaker_tmt_frame_settings": {
        "table": "tcc_tmt_settings",
        "columns": {
            "setting_id": "id",
            "frame_size_id": "frame_id",
            "setting_value": "value",
            "setting_desc": "label",
            "tolerance_low": "tol_lo",
            "tolerance_high": "tol_hi",
        },
    },
    "breaker_tmt_thermal_adj": {
        "table": "tcc_tmt_thermal_adj",
        "columns": {
            "thermal_adj_id": "id",
            "frame_size_id": "frame_id",
            "thermal_adj_setting": "adjustment",
        },
    },
    # EMT Tables
    "emt": {
        "table": "tcc_emt",
        "columns": {
            "id": "id",
            "mfr_id": "manufacturer_id",
            "type": "type_name",
            "style": "style_name",
            "tcc_number": "tcc_number",
            "note": "notes",
            "trip_char": "trip_char",
            "trip_plug": "trip_plug",
        },
    },
    "emt_frames": {
        "table": "tcc_emt_frames",
        "columns": {
            "id": "id",
            "style_id": "emt_id",
            "frame_size": "frame_size",
            "frame_desc": "frame_desc",
            "ordinal": "ordinal",
        },
    },
    "emt_frame_amps": {
        "table": "tcc_emt_frame_amps",
        "columns": {
            "frame_id": "frame_id",
            "trip_amp": "rating",
        },
    },
    "emt_sections": {
        "table": "tcc_emt_sections",
        "columns": {
            "id": "id",
            "name": "name",
            "frame_id": "frame_id",
            "sec_char": "sec_char",
            "curve_type": "curve_type",
            "pickup_calc": "pickup_calc",
            "pickup_toler_low": "pickup_tol_lo",
            "pickup_toler_high": "pickup_tol_hi",
            "pickup_setting": "pickup_setting",
            "step_size": "step_size",
            "current_calc": "current_calc",
            "delay_clr_curve": "delay_clr_curve",
            "delay_open_time": "delay_open_time",
            "delay_clear_time": "delay_clear_time",
            "open_curve_radius": "open_curve_radius",
            "clear_curve_radius": "clear_curve_radius",
        },
    },
    "emt_band_names": {
        "table": "tcc_emt_band_names",
        "columns": {
            "id": "id",
            "sec_id": "section_id",
            "band_name": "band_name",
            "ordinal": "ordinal",
            "current_at": "current_at",
        },
    },
    "emt_pickups": {
        "table": "tcc_emt_pickups",
        "columns": {
            "sec_id": "section_id",
            "setting": "setting",
            "description": "description",
        },
    },
    "emt_curves": {
        "table": "tcc_emt_curves",
        "columns": {
            "parent_id": "band_id",
            "class": "class",
            "time": "time_sec",
            "amps": "current_amp",
        },
    },
    # ETU Core
    "sst_plugs": {
        "table": "tcc_etu_plugs",
        "columns": {"plug_id": "id", "style_id": "trip_style_id", "plug_value": "value"},
    },
    "sst_sensors": {
        "table": "tcc_etu_sensors",
        "columns": {
            "sensor_id": "id",
            "style_id": "trip_style_id",
            "sensor_value": "rating",
            "sensor_desc": "description",
            "ltpu_section_name": "ltpu_name",
            "ltpu_calc_method": "ltpu_calc",
            "ltpu_tolerance_high": "ltpu_tol_hi",
            "ltpu_tolerance_low": "ltpu_tol_lo",
            "ltpu_step_size": "ltpu_step",
            "ltd_section_name": "ltd_name",
            "stpu_section_name": "stpu_name",
            "stpu_calc_method": "stpu_calc",
            "stpu_tolerance_high": "stpu_tol_hi",
            "stpu_tolerance_low": "stpu_tol_lo",
            "stpu_step_size": "stpu_step",
            "inst_section_name": "inst_name",
            "inst_calc_method": "inst_calc",
            "inst_tolerance_high": "inst_tol_hi",
            "inst_tolerance_low": "inst_tol_lo",
            "gfpu_section_name": "gfpu_name",
            "gfpu_calc_method": "gfpu_calc",
        },
    },
    # ETU Pickup Tables
    "sst_ltpu_settings": {
        "table": "tcc_etu_ltpu_pickups",
        "columns": {
            "ltpu_setting_id": "id",
            "sensor_id": "sensor_id",
            "setting_value": "value",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    "sst_ltpu_multipliers": {
        "table": "tcc_etu_ltpu_multipliers",
        "columns": {
            "multiplier_id": "id",
            "sensor_id": "sensor_id",
            "multiplier_c": "c_value",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    "sst_stpu_settings": {
        "table": "tcc_etu_stpu_pickups",
        "columns": {
            "stpu_setting_id": "id",
            "sensor_id": "sensor_id",
            "setting_desc": "label",
            "setting_value": "value",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    "sst_inst_settings": {
        "table": "tcc_etu_inst_pickups",
        "columns": {
            "inst_setting_id": "id",
            "sensor_id": "sensor_id",
            "setting_desc": "label",
            "setting_value": "value",
            "setting_mode": "mode",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    "sst_gfpu_settings": {
        "table": "tcc_etu_gfpu_pickups",
        "columns": {
            "gfpu_setting_id": "id",
            "sensor_id": "sensor_id",
            "setting_desc": "label",
            "setting_value": "value",
            "setting_mode": "mode",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    # ETU Delay Bands
    "sst_ltd_settings": {
        "table": "tcc_etu_ltd_bands",
        "columns": {
            "ltd_setting_id": "id",
            "sensor_id": "sensor_id",
            "ordinal": "ordinal",
            "delay_band": "band",
            "delay_band_display": "band_label",
            "ltd_open": "open_time",
            "ltd_clear": "clear_time",
            "i_open": "i_open",
            "i_clear": "i_clear",
            "t_open": "t_open",
            "t_clear": "t_clear",
            "i2x": "i2x",
            "ltd_x": "exp_x",
            "ltd_k": "const_k",
            "ltd_sgf": "sgf",
            "ltd_lowpu": "low_pickup",
            "ltd_khi": "const_k_hi",
            "curve_id": "curve_id",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    "sst_std_settings": {
        "table": "tcc_etu_std_bands",
        "columns": {
            "std_setting_id": "id",
            "sensor_id": "sensor_id",
            "ordinal": "ordinal",
            "delay_band": "band",
            "delay_band_display": "band_label",
            "std_open": "open_time",
            "std_clear": "clear_time",
            "i_open": "i_open",
            "i_clear": "i_clear",
            "t_open": "t_open",
            "t_clear": "t_clear",
            "i2x": "i2x",
            "std_x": "exp_x",
            "std_k": "const_k",
            "std_sgf": "sgf",
            "std_lowpu": "low_pickup",
            "std_khi": "const_k_hi",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    "sst_gfd_settings": {
        "table": "tcc_etu_gfd_bands",
        "columns": {
            "gfd_setting_id": "id",
            "sensor_id": "sensor_id",
            "ordinal": "ordinal",
            "delay_band": "band",
            "delay_band_display": "band_label",
            "gfd_open": "open_time",
            "gfd_clear": "clear_time",
            "i_open": "i_open",
            "i_clear": "i_clear",
            "t_open": "t_open",
            "t_clear": "t_clear",
            "i2x": "i2x",
            "gfd_x": "exp_x",
            "gfd_k": "const_k",
            "gfd_sgf": "sgf",
            "gfd_lowpu": "low_pickup",
            "gfd_khi": "const_k_hi",
            "is_default": "is_default",
            "sort_order": "sort_order",
        },
    },
    # ETU Equations
    "sst_std_inverse_equations": {
        "table": "tcc_etu_std_equations",
        "columns": {
            "equation_id": "id",
            "sensor_id": "sensor_id",
            "ordinal": "ordinal",
            "equation_desc": "label",
            "in_out": "in_out",
            "fd_open_eq": "fd_open_eq",
            "fd_open_1": "fd_open_1",
            "fd_open_2": "fd_open_2",
            "fd_open_3": "fd_open_3",
            "fd_open_4": "fd_open_4",
            "fd_open_5": "fd_open_5",
            "fd_open_6": "fd_open_6",
            "fd_open_i_calc": "fd_open_i_calc",
            "fd_clear_eq": "fd_clear_eq",
            "fd_clear_1": "fd_clear_1",
            "fd_clear_2": "fd_clear_2",
            "fd_clear_3": "fd_clear_3",
            "fd_clear_4": "fd_clear_4",
            "fd_clear_5": "fd_clear_5",
            "fd_clear_6": "fd_clear_6",
            "fd_clear_i_calc": "fd_clear_i_calc",
            "id_open_eq": "id_open_eq",
            "id_open_1": "id_open_1",
            "id_open_2": "id_open_2",
            "id_open_3": "id_open_3",
            "id_open_4": "id_open_4",
            "id_open_5": "id_open_5",
            "id_open_6": "id_open_6",
            "id_open_i_calc": "id_open_i_calc",
            "id_clear_eq": "id_clear_eq",
            "id_clear_1": "id_clear_1",
            "id_clear_2": "id_clear_2",
            "id_clear_3": "id_clear_3",
            "id_clear_4": "id_clear_4",
            "id_clear_5": "id_clear_5",
            "id_clear_6": "id_clear_6",
            "id_clear_i_calc": "id_clear_i_calc",
        },
    },
    "sst_gfd_inverse_equations": {
        "table": "tcc_etu_gfd_equations",
        "columns": {
            "equation_id": "id",
            "sensor_id": "sensor_id",
            "ordinal": "ordinal",
            "equation_desc": "label",
            "in_out": "in_out",
            "fd_open_eq": "fd_open_eq",
            "fd_open_1": "fd_open_1",
            "fd_open_2": "fd_open_2",
            "fd_open_3": "fd_open_3",
            "fd_open_4": "fd_open_4",
            "fd_open_5": "fd_open_5",
            "fd_open_6": "fd_open_6",
            "fd_open_i_calc": "fd_open_i_calc",
            "fd_clear_eq": "fd_clear_eq",
            "fd_clear_1": "fd_clear_1",
            "fd_clear_2": "fd_clear_2",
            "fd_clear_3": "fd_clear_3",
            "fd_clear_4": "fd_clear_4",
            "fd_clear_5": "fd_clear_5",
            "fd_clear_6": "fd_clear_6",
            "fd_clear_i_calc": "fd_clear_i_calc",
            "id_open_eq": "id_open_eq",
            "id_open_1": "id_open_1",
            "id_open_2": "id_open_2",
            "id_open_3": "id_open_3",
            "id_open_4": "id_open_4",
            "id_open_5": "id_open_5",
            "id_open_6": "id_open_6",
            "id_open_i_calc": "id_open_i_calc",
            "id_clear_eq": "id_clear_eq",
            "id_clear_1": "id_clear_1",
            "id_clear_2": "id_clear_2",
            "id_clear_3": "id_clear_3",
            "id_clear_4": "id_clear_4",
            "id_clear_5": "id_clear_5",
            "id_clear_6": "id_clear_6",
            "id_clear_i_calc": "id_clear_i_calc",
        },
    },
    # ETU Curves & Params
    "sst_inst_curves": {
        "table": "tcc_etu_inst_curves",
        "columns": {
            "curve_id": "id",
            "sensor_id": "sensor_id",
            "ordinal": "ordinal",
            "curve_type": "class",
            "current_point": "current_amp",
            "time_point": "time_sec",
        },
    },
    "sst_sensor_parameters": {
        "table": "tcc_etu_sensor_params",
        "columns": {
            "parameter_id": "id",
            "sensor_id": "sensor_id",
            "section": "section",
            "param_index": "idx",
            "param_value": "value",
            "curve_id": "curve_id",
        },
    },
    "sst_sensor_sec2_params": {
        "table": "tcc_etu_ltd_params",
        "columns": {
            "sec2_param_id": "id",
            "sensor_id": "sensor_id",
            "curve_id": "curve_id",
            "curve_name": "curve_name",
            "ordinal": "ordinal",
            "setting_method": "method",
            "sec2_ltf": "ltf",
            "tol_high": "tol_hi",
            "tol_low": "tol_lo",
            "setting_val": "value",
            "setting_type": "type",
            "slope": "slope",
            "step_size": "step",
            "dly_pty": "delay_priority",
            "force_i2x_out": "force_i2x_out",
        },
    },
    "sst_stpu_overrides": {
        "table": "tcc_etu_stpu_overrides",
        "columns": {
            "override_id": "id",
            "sensor_id": "sensor_id",
            "override_type": "type",
            "override_value": "value",
            "description": "description",
        },
    },
    "sst_sensor_maintenance": {
        "table": "tcc_etu_sensor_maint",
        "columns": {
            "maintenance_id": "id",
            "sensor_id": "sensor_id",
            "alarm_type": "alarm_type",
            "alarm_threshold": "alarm_threshold",
            "alarm_enabled": "alarm_enabled",
            "maintenance_mode_available": "maint_available",
            "maintenance_mode_ltpu_reduction": "maint_ltpu_reduction",
            "maintenance_mode_stpu_reduction": "maint_stpu_reduction",
            "maintenance_mode_inst_reduction": "maint_inst_reduction",
            "maintenance_params": "params_json",
        },
    },
}

    Source: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL
    Target: DATABASE_URL
    "manufacturers",
    "trip_types",
    "trip_styles",
    "breaker_iccb",
    "breaker_iccb_styles",
    "breaker_mccb",
    "breaker_mccb_styles",
    "breaker_pcb",
    "breaker_pcb_styles",
    "breaker_tmt_frame_sizes",
    "breaker_tmt_frame_amps",
    "breaker_tmt_frame_curves",
    "breaker_tmt_frame_settings",
    "breaker_tmt_thermal_adj",
    "sst_plugs",
    "sst_sensors",
    "sst_ltpu_settings",
    "sst_ltpu_multipliers",
    "sst_stpu_settings",
    "sst_inst_settings",
    "sst_gfpu_settings",
    "sst_ltd_settings",
    "sst_std_settings",
    "sst_gfd_settings",
    "sst_std_inverse_equations",
    "sst_gfd_inverse_equations",
    "sst_inst_curves",
    "sst_sensor_parameters",
    "sst_sensor_sec2_params",
    "sst_stpu_overrides",
    "sst_sensor_maintenance",
]


# ============================================================================
# UTILITIES
# ============================================================================


def get_source_columns(conn, src_table: str) -> List[str]:
    """Get list of column names from source table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
            """,
            (src_table,),
        )
        return [row[0] for row in cur.fetchall()]


def get_target_columns(conn, tgt_table: str) -> List[str]:
    """Get list of column names from target table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
            """,
            (tgt_table,),
        )
        return [row[0] for row in cur.fetchall()]


def build_target_columns(src_cols: List[str], col_mapping: Dict[str, str]) -> List[str]:
    """Map source column names to target column names."""
    return [col_mapping.get(col, col) for col in src_cols]


def count_rows(conn, table: str) -> int:
    """Count rows in a table."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]


def fetch_all_data(conn, src_table: str, src_cols: List[str]) -> List[Tuple]:
    """Fetch all rows from source table."""
    col_list = ", ".join(f'"{col}"' for col in src_cols)
    with conn.cursor() as cur:
        cur.execute(f"SELECT {col_list} FROM {src_table}")
        return cur.fetchall()


def build_breaker_class_lookup(conn) -> Dict[int, str]:
    """
    Query all style_ids from the 3 breaker style tables and build a lookup.
    Returns {style_id: 'iccb'|'mccb'|'pcb'}
    """
    lookup = {}
    with conn.cursor() as cur:
        # ICCB styles
        cur.execute("SELECT style_id FROM breaker_iccb_styles")
        for (style_id,) in cur.fetchall():
            lookup[style_id] = "iccb"

        # MCCB styles
        cur.execute("SELECT style_id FROM breaker_mccb_styles")
        for (style_id,) in cur.fetchall():
            lookup[style_id] = "mccb"

        # PCB styles
        cur.execute("SELECT style_id FROM breaker_pcb_styles")
        for (style_id,) in cur.fetchall():
            lookup[style_id] = "pcb"

    return lookup


def insert_small_table(
    src_conn,
    tgt_conn,
    src_table: str,
    tgt_table: str,
    src_cols: List[str],
    tgt_cols: List[str],
    dry_run: bool = False,
) -> int:
    """Insert data using batch INSERT VALUES with ON CONFLICT DO NOTHING."""
    rows = fetch_all_data(src_conn, src_table, src_cols)
    if not rows:
        return 0

    if dry_run:
        return len(rows)

    # Convert dict values to JSON strings for psycopg2
    cleaned_rows = []
    for row in rows:
        cleaned_rows.append(
            tuple(json.dumps(v) if isinstance(v, dict) else v for v in row)
        )

    col_list = ", ".join(f'"{ col}"' for col in tgt_cols)

    with tgt_conn.cursor() as cur:
        execute_values(
            cur,
            f"INSERT INTO {tgt_table} ({col_list}) VALUES %s ON CONFLICT DO NOTHING",
            cleaned_rows,
            page_size=2000,
        )
    tgt_conn.commit()
    return len(rows)


def insert_large_table(
    src_conn,
    tgt_conn,
    src_table: str,
    tgt_table: str,
    src_cols: List[str],
    tgt_cols: List[str],
    batch_size: int = 50000,
    dry_run: bool = False,
) -> int:
    """Insert data for a large table using batch INSERT with ON CONFLICT DO NOTHING."""
    col_list = ", ".join(f'"{col}"' for col in tgt_cols)

    # Fetch all rows from source
    rows = fetch_all_data(src_conn, src_table, src_cols)
    total_rows = len(rows)

    if not total_rows:
        return 0

    if dry_run:
        return total_rows

    # Convert dict values to JSON strings
    cleaned_rows = []
    for row in rows:
        cleaned_rows.append(
            tuple(json.dumps(v) if isinstance(v, dict) else v for v in row)
        )

    # Insert in batches using execute_values with ON CONFLICT
    with tgt_conn.cursor() as cur:
        for i in range(0, len(cleaned_rows), batch_size):
            batch = cleaned_rows[i : i + batch_size]
            execute_values(
                cur,
                f"INSERT INTO {tgt_table} ({col_list}) VALUES %s ON CONFLICT DO NOTHING",
                batch,
                page_size=2000,
            )
    tgt_conn.commit()
    return total_rows


def insert_with_breaker_class_backfill(
    src_conn,
    tgt_conn,
    src_table: str,
    tgt_table: str,
    src_cols: List[str],
    tgt_cols: List[str],
    breaker_lookup: Dict[int, str],
    dry_run: bool = False,
) -> int:
    """Insert tcc_tmt_frames with breaker_class backfill."""
    rows = fetch_all_data(src_conn, src_table, src_cols)
    if not rows:
        return 0

    # Find the index of style_id in src_cols
    style_id_idx = src_cols.index("style_id")

    # Find where breaker_class should be inserted in target
    # It's after breaker_style_id in the target schema
    breaker_class_data = []
    for row in rows:
        style_id = row[style_id_idx]
        breaker_class = breaker_lookup.get(style_id, "unknown")
        breaker_class_data.append(breaker_class)

    if dry_run:
        return len(rows)

    # Filter out rows where size (frame_size) is NULL — target has NOT NULL constraint
    size_idx = src_cols.index("frame_size") if "frame_size" in src_cols else None
    
    extended_rows = []
    for row, bc in zip(rows, breaker_class_data):
        if size_idx is not None and row[size_idx] is None:
            continue  # skip rows with NULL size
        extended_rows.append(row + (bc,))

    col_list_str = ", ".join(f'"{ col}"' for col in tgt_cols)
    col_list_str += ', "breaker_class"'

    with tgt_conn.cursor() as cur:
        execute_values(
            cur,
            f"INSERT INTO {tgt_table} ({col_list_str}) VALUES %s ON CONFLICT DO NOTHING",
            extended_rows,
            page_size=2000,
        )
    tgt_conn.commit()
    return len(extended_rows)


def reset_sequences(conn, dry_run: bool = False):
    """Reset all SERIAL sequences to max(id)+1 for each table."""
    tables = [cfg["table"] for cfg in TABLE_CONFIGS.values()]

    if dry_run:
        print("\nDRY RUN: Would reset sequences for all tables")
        return

    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table}), 1) + 1
                    )
                    """
                )
            except psycopg2.errors.UndefinedTable:
                # Table doesn't exist, skip
                pass
            except Exception as e:
                print(f"Warning: Could not reset sequence for {table}: {e}")
    conn.commit()


# ============================================================================
# MAIN TRANSFER LOGIC
# ============================================================================


def transfer_data(dry_run: bool = False, verbose: bool = False):
    """Execute the full data transfer."""
    print("\n" + "=" * 80)
    print("TCC v5 DATA TRANSFER - PostgreSQL to Supabase")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dry_run:
        print("MODE: DRY RUN (no data will be written)")
    print()

    # Connection strings
    source_url = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL")
    if not source_url:
        raise RuntimeError("Missing required environment variable: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL")
    target_url = require_env("DATABASE_URL")

    # Connect to databases
    print("Connecting to source database...")
    try:
        src_conn = psycopg2.connect(source_url)
        print(f"✓ Connected to source: {source_url.split('@')[1]}")
    except Exception as e:
        print(f"✗ Failed to connect to source: {e}")
        return False

    print("Connecting to target database...")
    try:
        tgt_conn = psycopg2.connect(target_url)
        print(f"✓ Connected to target: {describe_connection_target(target_url)}")
    except Exception as e:
        print(f"✗ Failed to connect to target: {e}")
        src_conn.close()
        return False

    print()
    print("=" * 80)
    print("TRANSFER PROGRESS")
    print("=" * 80)
    print()

    total_rows_transferred = 0
    start_time = time.time()

    # Truncate all target tables in reverse order to respect FK constraints
    if not dry_run:
        print("Clearing target tables...")
        with tgt_conn.cursor() as cur:
            for src_table_name in reversed(TABLE_ORDER):
                tgt_table_name = TABLE_CONFIGS[src_table_name]["table"]
                try:
                    cur.execute(f"TRUNCATE {tgt_table_name} CASCADE")
                except Exception as e:
                    tgt_conn.rollback()
                    print(f"  Warning: Could not truncate {tgt_table_name}: {e}")
        tgt_conn.commit()
        print("✓ Target tables cleared")

        # Disable FK constraint checks for the transfer session
        print("Disabling FK constraint checks...")
        with tgt_conn.cursor() as cur:
            cur.execute("SET session_replication_role = 'replica'")
        tgt_conn.commit()
        print("✓ FK constraints disabled\n")

    # Build breaker_class lookup for TMT frames
    breaker_lookup = build_breaker_class_lookup(src_conn)
    if verbose:
        print(f"Breaker class lookup: {len(breaker_lookup)} style IDs mapped\n")

    # Transfer each table
    for src_table_name in TABLE_ORDER:
        config = TABLE_CONFIGS[src_table_name]
        tgt_table_name = config["table"]
        col_mapping = config["columns"]

        # Use only mapped columns from source (not all source columns)
        src_cols = list(col_mapping.keys())
        tgt_cols = [col_mapping[col] for col in src_cols]

        # Count rows
        try:
            row_count = count_rows(src_conn, src_table_name)
        except Exception as e:
            print(f"⊘ {src_table_name}: Table not found in source - {e}")
            continue

        if row_count == 0:
            print(f"⊘ {src_table_name}: 0 rows (skipped)")
            continue

        # Time the transfer
        table_start = time.time()

        try:
            # Handle special cases
            if config.get("special") == "breaker_class_backfill":
                rows_inserted = insert_with_breaker_class_backfill(
                    src_conn,
                    tgt_conn,
                    src_table_name,
                    tgt_table_name,
                    src_cols,
                    tgt_cols,
                    breaker_lookup,
                    dry_run=dry_run,
                )
            elif row_count >= 10000:
                # Large table: use COPY
                rows_inserted = insert_large_table(
                    src_conn,
                    tgt_conn,
                    src_table_name,
                    tgt_table_name,
                    src_cols,
                    tgt_cols,
                    dry_run=dry_run,
                )
            else:
                # Small table: use INSERT
                rows_inserted = insert_small_table(
                    src_conn,
                    tgt_conn,
                    src_table_name,
                    tgt_table_name,
                    src_cols,
                    tgt_cols,
                    dry_run=dry_run,
                )

            elapsed = time.time() - table_start
            total_rows_transferred += rows_inserted

            # Print progress
            method = "COPY" if row_count >= 10000 else "INSERT"
            print(f"✓ {src_table_name}: {rows_inserted:,} rows ({elapsed:.2f}s) [{method}]")

            if verbose:
                print(f"  Target table: {tgt_table_name}")
                print(f"  Columns mapped: {len(col_mapping)}")
                print()

        except Exception as e:
            print(f"✗ {src_table_name}: Transfer failed - {e}")
            tgt_conn.rollback()

    # Reset sequences
    print()
    print("=" * 80)
    print("FINALIZING")
    print("=" * 80)
    print()

    # Re-enable FK constraint checks
    if not dry_run:
        print("Re-enabling FK constraint checks...")
        with tgt_conn.cursor() as cur:
            cur.execute("SET session_replication_role = 'origin'")
        tgt_conn.commit()
        print("✓ FK constraints re-enabled")

    print("Resetting sequences...")
    reset_sequences(tgt_conn, dry_run=dry_run)
    print("✓ Sequences reset")

    # Summary
    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print("TRANSFER COMPLETE")
    print("=" * 80)
    print(f"Total rows transferred: {total_rows_transferred:,}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Rate: {total_rows_transferred / total_time:.0f} rows/sec")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Close connections
    src_conn.close()
    tgt_conn.close()

    return True


# ============================================================================
# ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transfer data from local PostgreSQL to Supabase with column renaming"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview transfer without writing data",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed transfer information",
    )

    args = parser.parse_args()

    success = transfer_data(dry_run=args.dry_run, verbose=args.verbose)
    sys.exit(0 if success else 1)
