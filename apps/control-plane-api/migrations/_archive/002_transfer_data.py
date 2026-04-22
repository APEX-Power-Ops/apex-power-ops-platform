#!/usr/bin/env python3
"""
TCC v5 Data Transfer Script
Migrates ~2.5M rows from local PostgreSQL to Supabase with column renaming,
batching, and performance optimizations.

Usage:
    python 002_transfer_data.py [target_connection_string]
    
If target_connection_string is not provided, you will be prompted for it.
"""

import sys
import time
import argparse
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

SOURCE_DSN = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL")
if not SOURCE_DSN:
    raise RuntimeError("Missing required environment variable: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL")
BATCH_SIZE = 50000
LARGE_TABLE_THRESHOLD = 10000

# Table mappings: source → target with column renames
TABLES = [
    # REFERENCE
    {
        "source": "manufacturers",
        "target": "tcc_manufacturers",
        "columns": {"mfg_id": "id", "mfg_name": "name", "created_at": "created_at"}
    },
    {
        "source": "trip_types",
        "target": "tcc_trip_types",
        "columns": {"type_id": "id", "mfg_id": "manufacturer_id", "type_name": "name", "created_at": "created_at"}
    },
    {
        "source": "trip_styles",
        "target": "tcc_trip_styles",
        "columns": {"style_id": "id", "type_id": "trip_type_id", "mfg_id": "manufacturer_id", "style_name": "name", "notes": "notes", "tcc_number": "tcc_number", "created_at": "created_at"}
    },

    # BREAKERS
    {
        "source": "breaker_iccb",
        "target": "tcc_brk_iccb",
        "columns": {"iccb_id": "id", "mfg_id": "manufacturer_id", "iccb_type": "name", "standard_type": "standard", "created_at": "created_at"}
    },
    {
        "source": "breaker_iccb_styles",
        "target": "tcc_brk_iccb_styles",
        "columns": {"style_id": "id", "iccb_id": "breaker_id", "frame_name": "frame", "voltage_id": "voltage_id", "kaic_480v": "kaic_480v", "kaic_600v": "kaic_600v", "standard_type": "standard", "notes": "notes", "created_at": "created_at"}
    },
    {
        "source": "breaker_mccb",
        "target": "tcc_brk_mccb",
        "columns": {"mccb_id": "id", "mfg_id": "manufacturer_id", "mccb_type": "name", "standard_type": "standard", "created_at": "created_at"}
    },
    {
        "source": "breaker_mccb_styles",
        "target": "tcc_brk_mccb_styles",
        "columns": {"style_id": "id", "mccb_id": "breaker_id", "frame_name": "frame", "voltage_id": "voltage_id", "kaic_240v": "kaic_240v", "kaic_480v": "kaic_480v", "kaic_600v": "kaic_600v", "poles": "poles", "standard_type": "standard", "interrupt_class": "interrupt_class", "notes": "notes", "created_at": "created_at"}
    },
    {
        "source": "breaker_pcb",
        "target": "tcc_brk_pcb",
        "columns": {"pcb_id": "id", "mfg_id": "manufacturer_id", "pcb_type": "name", "standard_type": "standard", "created_at": "created_at"}
    },
    {
        "source": "breaker_pcb_styles",
        "target": "tcc_brk_pcb_styles",
        "columns": {"style_id": "id", "pcb_id": "breaker_id", "frame_name": "frame", "voltage_id": "voltage_id", "kaic_480v": "kaic_480v", "kaic_600v": "kaic_600v", "standard_type": "standard", "notes": "notes", "created_at": "created_at"}
    },

    # TMT
    {
        "source": "breaker_tmt_frame_sizes",
        "target": "tcc_tmt_frames",
        "columns": {"frame_size_id": "id", "style_id": "breaker_style_id", "frame_size": "size", "created_at": "created_at"},
        "extra_columns": {"breaker_class": "DERIVE"}
    },
    {
        "source": "breaker_tmt_frame_amps",
        "target": "tcc_tmt_amps",
        "columns": {"frame_amp_id": "id", "frame_size_id": "frame_id", "amp_rating": "rating", "max_override": "max_override", "created_at": "created_at"}
    },
    {
        "source": "breaker_tmt_frame_curves",
        "target": "tcc_tmt_curves",
        "columns": {"curve_id": "id", "frame_size_id": "frame_id", "curve_class": "class", "time_seconds": "time_sec", "current_amps": "current_amp", "created_at": "created_at"}
    },
    {
        "source": "breaker_tmt_frame_settings",
        "target": "tcc_tmt_settings",
        "columns": {"setting_id": "id", "frame_size_id": "frame_id", "setting_value": "value", "setting_desc": "label", "tolerance_low": "tol_lo", "tolerance_high": "tol_hi", "created_at": "created_at"}
    },
    {
        "source": "breaker_tmt_thermal_adj",
        "target": "tcc_tmt_thermal_adj",
        "columns": {"thermal_adj_id": "id", "frame_size_id": "frame_id", "thermal_adj_setting": "adjustment", "created_at": "created_at"}
    },

    # EMT
    {
        "source": "emt",
        "target": "tcc_emt",
        "columns": {"id": "id", "mfr_id": "manufacturer_id", "type": "type_name", "style": "style_name", "tcc_number": "tcc_number", "note": "notes", "trip_char": "trip_char", "trip_plug": "trip_plug", "created_at": "created_at"}
    },
    {
        "source": "emt_frames",
        "target": "tcc_emt_frames",
        "columns": {"id": "id", "style_id": "emt_id", "frame_size": "frame_size", "frame_desc": "frame_desc", "ordinal": "ordinal", "created_at": "created_at"}
    },
    {
        "source": "emt_frame_amps",
        "target": "tcc_emt_frame_amps",
        "columns": {"frame_id": "frame_id", "trip_amp": "rating", "created_at": "created_at"}
    },
    {
        "source": "emt_sections",
        "target": "tcc_emt_sections",
        "columns": {"id": "id", "name": "name", "frame_id": "frame_id", "sec_char": "sec_char", "curve_type": "curve_type", "pickup_calc": "pickup_calc", "pickup_toler_low": "pickup_tol_lo", "pickup_toler_high": "pickup_tol_hi", "pickup_setting": "pickup_setting", "step_size": "step_size", "current_calc": "current_calc", "delay_clr_curve": "delay_clr_curve", "delay_open_time": "delay_open_time", "delay_clear_time": "delay_clear_time", "open_curve_radius": "open_curve_radius", "clear_curve_radius": "clear_curve_radius", "created_at": "created_at"}
    },
    {
        "source": "emt_band_names",
        "target": "tcc_emt_band_names",
        "columns": {"id": "id", "sec_id": "section_id", "band_name": "band_name", "ordinal": "ordinal", "current_at": "current_at", "created_at": "created_at"}
    },
    {
        "source": "emt_pickups",
        "target": "tcc_emt_pickups",
        "columns": {"sec_id": "section_id", "setting": "setting", "description": "description", "created_at": "created_at"}
    },
    {
        "source": "emt_curves",
        "target": "tcc_emt_curves",
        "columns": {"parent_id": "band_id", "class": "class", "time": "time_sec", "amps": "current_amp", "created_at": "created_at"}
    },

    # ETU CORE
    {
        "source": "sst_plugs",
        "target": "tcc_etu_plugs",
        "columns": {"plug_id": "id", "style_id": "trip_style_id", "plug_value": "value", "created_at": "created_at"}
    },
    {
        "source": "sst_sensors",
        "target": "tcc_etu_sensors",
        "columns": {"sensor_id": "id", "style_id": "trip_style_id", "sensor_value": "rating", "sensor_desc": "description", "ltpu_section_name": "ltpu_name", "ltpu_calc_method": "ltpu_calc", "ltpu_tolerance_high": "ltpu_tol_hi", "ltpu_tolerance_low": "ltpu_tol_lo", "ltpu_step_size": "ltpu_step", "ltd_section_name": "ltd_name", "stpu_section_name": "stpu_name", "stpu_calc_method": "stpu_calc", "stpu_tolerance_high": "stpu_tol_hi", "stpu_tolerance_low": "stpu_tol_lo", "stpu_step_size": "stpu_step", "inst_section_name": "inst_name", "inst_calc_method": "inst_calc", "inst_tolerance_high": "inst_tol_hi", "inst_tolerance_low": "inst_tol_lo", "gfpu_section_name": "gfpu_name", "gfpu_calc_method": "gfpu_calc", "created_at": "created_at"}
    },

    # ETU PICKUPS
    {
        "source": "sst_ltpu_settings",
        "target": "tcc_etu_ltpu_pickups",
        "columns": {"ltpu_setting_id": "id", "sensor_id": "sensor_id", "setting_value": "value", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },
    {
        "source": "sst_ltpu_multipliers",
        "target": "tcc_etu_ltpu_multipliers",
        "columns": {"multiplier_id": "id", "sensor_id": "sensor_id", "multiplier_c": "c_value", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },
    {
        "source": "sst_stpu_settings",
        "target": "tcc_etu_stpu_pickups",
        "columns": {"stpu_setting_id": "id", "sensor_id": "sensor_id", "setting_desc": "label", "setting_value": "value", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },
    {
        "source": "sst_inst_settings",
        "target": "tcc_etu_inst_pickups",
        "columns": {"inst_setting_id": "id", "sensor_id": "sensor_id", "setting_desc": "label", "setting_value": "value", "setting_mode": "mode", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },
    {
        "source": "sst_gfpu_settings",
        "target": "tcc_etu_gfpu_pickups",
        "columns": {"gfpu_setting_id": "id", "sensor_id": "sensor_id", "setting_desc": "label", "setting_value": "value", "setting_mode": "mode", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },

    # ETU DELAY BANDS
    {
        "source": "sst_ltd_settings",
        "target": "tcc_etu_ltd_bands",
        "columns": {"ltd_setting_id": "id", "sensor_id": "sensor_id", "ordinal": "ordinal", "delay_band": "band", "delay_band_display": "band_label", "ltd_open": "open_time", "ltd_clear": "clear_time", "i_open": "i_open", "i_clear": "i_clear", "t_open": "t_open", "t_clear": "t_clear", "i2x": "i2x", "ltd_x": "exp_x", "ltd_k": "const_k", "ltd_sgf": "sgf", "ltd_lowpu": "low_pickup", "ltd_khi": "const_k_hi", "curve_id": "curve_id", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },
    {
        "source": "sst_std_settings",
        "target": "tcc_etu_std_bands",
        "columns": {"std_setting_id": "id", "sensor_id": "sensor_id", "ordinal": "ordinal", "delay_band": "band", "delay_band_display": "band_label", "std_open": "open_time", "std_clear": "clear_time", "i_open": "i_open", "i_clear": "i_clear", "t_open": "t_open", "t_clear": "t_clear", "i2x": "i2x", "std_x": "exp_x", "std_k": "const_k", "std_sgf": "sgf", "std_lowpu": "low_pickup", "std_khi": "const_k_hi", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },
    {
        "source": "sst_gfd_settings",
        "target": "tcc_etu_gfd_bands",
        "columns": {"gfd_setting_id": "id", "sensor_id": "sensor_id", "ordinal": "ordinal", "delay_band": "band", "delay_band_display": "band_label", "gfd_open": "open_time", "gfd_clear": "clear_time", "i_open": "i_open", "i_clear": "i_clear", "t_open": "t_open", "t_clear": "t_clear", "i2x": "i2x", "gfd_x": "exp_x", "gfd_k": "const_k", "gfd_sgf": "sgf", "gfd_lowpu": "low_pickup", "gfd_khi": "const_k_hi", "is_default": "is_default", "sort_order": "sort_order", "created_at": "created_at"}
    },

    # ETU EQUATIONS
    {
        "source": "sst_std_inverse_equations",
        "target": "tcc_etu_std_equations",
        "columns": {"equation_id": "id", "sensor_id": "sensor_id", "ordinal": "ordinal", "equation_desc": "label", "in_out": "in_out", "fd_open_eq": "fd_open_eq", "fd_open_1": "fd_open_1", "fd_open_2": "fd_open_2", "fd_open_3": "fd_open_3", "fd_open_4": "fd_open_4", "fd_open_5": "fd_open_5", "fd_open_6": "fd_open_6", "fd_open_i_calc": "fd_open_i_calc", "fd_clear_eq": "fd_clear_eq", "fd_clear_1": "fd_clear_1", "fd_clear_2": "fd_clear_2", "fd_clear_3": "fd_clear_3", "fd_clear_4": "fd_clear_4", "fd_clear_5": "fd_clear_5", "fd_clear_6": "fd_clear_6", "fd_clear_i_calc": "fd_clear_i_calc", "id_open_eq": "id_open_eq", "id_open_1": "id_open_1", "id_open_2": "id_open_2", "id_open_3": "id_open_3", "id_open_4": "id_open_4", "id_open_5": "id_open_5", "id_open_6": "id_open_6", "id_open_i_calc": "id_open_i_calc", "id_clear_eq": "id_clear_eq", "id_clear_1": "id_clear_1", "id_clear_2": "id_clear_2", "id_clear_3": "id_clear_3", "id_clear_4": "id_clear_4", "id_clear_5": "id_clear_5", "id_clear_6": "id_clear_6", "id_clear_i_calc": "id_clear_i_calc", "created_at": "created_at"}
    },
    {
        "source": "sst_gfd_inverse_equations",
        "target": "tcc_etu_gfd_equations",
        "columns": {"equation_id": "id", "sensor_id": "sensor_id", "ordinal": "ordinal", "equation_desc": "label", "in_out": "in_out", "fd_open_eq": "fd_open_eq", "fd_open_1": "fd_open_1", "fd_open_2": "fd_open_2", "fd_open_3": "fd_open_3", "fd_open_4": "fd_open_4", "fd_open_5": "fd_open_5", "fd_open_6": "fd_open_6", "fd_open_i_calc": "fd_open_i_calc", "fd_clear_eq": "fd_clear_eq", "fd_clear_1": "fd_clear_1", "fd_clear_2": "fd_clear_2", "fd_clear_3": "fd_clear_3", "fd_clear_4": "fd_clear_4", "fd_clear_5": "fd_clear_5", "fd_clear_6": "fd_clear_6", "fd_clear_i_calc": "fd_clear_i_calc", "id_open_eq": "id_open_eq", "id_open_1": "id_open_1", "id_open_2": "id_open_2", "id_open_3": "id_open_3", "id_open_4": "id_open_4", "id_open_5": "id_open_5", "id_open_6": "id_open_6", "id_open_i_calc": "id_open_i_calc", "id_clear_eq": "id_clear_eq", "id_clear_1": "id_clear_1", "id_clear_2": "id_clear_2", "id_clear_3": "id_clear_3", "id_clear_4": "id_clear_4", "id_clear_5": "id_clear_5", "id_clear_6": "id_clear_6", "id_clear_i_calc": "id_clear_i_calc", "created_at": "created_at"}
    },

    # ETU CURVES & PARAMS
    {
        "source": "sst_inst_curves",
        "target": "tcc_etu_inst_curves",
        "columns": {"curve_id": "id", "sensor_id": "sensor_id", "ordinal": "ordinal", "curve_type": "class", "current_point": "current_amp", "time_point": "time_sec", "created_at": "created_at"}
    },
    {
        "source": "sst_sensor_parameters",
        "target": "tcc_etu_sensor_params",
        "columns": {"parameter_id": "id", "sensor_id": "sensor_id", "section": "section", "param_index": "idx", "param_value": "value", "curve_id": "curve_id", "created_at": "created_at"}
    },
    {
        "source": "sst_sensor_sec2_params",
        "target": "tcc_etu_ltd_params",
        "columns": {"sec2_param_id": "id", "sensor_id": "sensor_id", "curve_id": "curve_id", "curve_name": "curve_name", "ordinal": "ordinal", "setting_method": "method", "sec2_ltf": "ltf", "tol_high": "tol_hi", "tol_low": "tol_lo", "setting_val": "value", "setting_type": "type", "slope": "slope", "step_size": "step", "dly_pty": "delay_priority", "force_i2x_out": "force_i2x_out", "created_at": "created_at"}
    },
    {
        "source": "sst_stpu_overrides",
        "target": "tcc_etu_stpu_overrides",
        "columns": {"override_id": "id", "sensor_id": "sensor_id", "override_type": "type", "override_value": "value", "description": "description", "created_at": "created_at"}
    },
    {
        "source": "sst_sensor_maintenance",
        "target": "tcc_etu_sensor_maint",
        "columns": {"maintenance_id": "id", "sensor_id": "sensor_id", "alarm_type": "alarm_type", "alarm_threshold": "alarm_threshold", "alarm_enabled": "alarm_enabled", "maintenance_mode_available": "maint_available", "maintenance_mode_ltpu_reduction": "maint_ltpu_reduction", "maintenance_mode_stpu_reduction": "maint_stpu_reduction", "maintenance_mode_inst_reduction": "maint_inst_reduction", "maintenance_params": "params_json", "created_at": "created_at"}
    },
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_target_dsn() -> str:
    """Get target connection string from command-line arg or prompt user."""
    parser = argparse.ArgumentParser(description="Migrate TCC v5 data to Supabase")
    parser.add_argument(
        "target_dsn",
        nargs="?",
        help="Target Supabase connection string"
    )
    args = parser.parse_args()
    
    if args.target_dsn:
        return args.target_dsn
    
    print("\n" + "="*70)
    print("TCC v5 Data Transfer - Target Connection Required")
    print("="*70)
    print("\nProvide your Supabase connection string.")
    print("Example: postgresql://user:password@db.supabase.co:5432/postgres")
    print()
    target_dsn = input("Target connection string: ").strip()
    
    if not target_dsn:
        print("ERROR: Connection string required")
        sys.exit(1)
    
    return target_dsn


def connect_db(dsn: str) -> psycopg2.extensions.connection:
    """Connect to a PostgreSQL database."""
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        print(f"ERROR: Failed to connect to {dsn}")
        print(f"Details: {e}")
        sys.exit(1)


def table_exists(conn: psycopg2.extensions.connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table_name,))
        return cur.fetchone()[0]


def get_row_count(conn: psycopg2.extensions.connection, table_name: str) -> int:
    """Get the number of rows in a table."""
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
            sql.Identifier(table_name)
        ))
        return cur.fetchone()[0]


def get_table_columns(conn: psycopg2.extensions.connection, table_name: str) -> set:
    """Get the set of column names for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s
        """, (table_name,))
        return {row[0] for row in cur.fetchall()}


def build_breaker_class_lookup(src_conn: psycopg2.extensions.connection) -> Dict[int, str]:
    """
    Build a lookup dictionary: style_id -> breaker_class.
    Checks membership in iccb_styles, mccb_styles, pcb_styles.
    Defaults to 'mccb' if no match found.
    """
    lookup = {}
    
    with src_conn.cursor() as cur:
        # Get ICCB styles
        cur.execute("SELECT style_id FROM breaker_iccb_styles")
        for (style_id,) in cur.fetchall():
            lookup[style_id] = "iccb"
        
        # Get MCCB styles
        cur.execute("SELECT style_id FROM breaker_mccb_styles")
        for (style_id,) in cur.fetchall():
            lookup[style_id] = "mccb"
        
        # Get PCB styles
        cur.execute("SELECT style_id FROM breaker_pcb_styles")
        for (style_id,) in cur.fetchall():
            lookup[style_id] = "pcb"
    
    return lookup


def transfer_table(
    src_conn: psycopg2.extensions.connection,
    tgt_conn: psycopg2.extensions.connection,
    table_config: Dict,
    breaker_class_lookup: Dict[int, str] = None
) -> Tuple[int, str, bool]:
    """
    Transfer a single table from source to target.
    Returns: (row_count, status_msg, success)
    """
    src_table = table_config["source"]
    tgt_table = table_config["target"]
    col_map = table_config["columns"]
    extra_cols = table_config.get("extra_columns", {})
    
    try:
        # Check if source table exists
        if not table_exists(src_conn, src_table):
            return 0, f"[SKIP] source table '{src_table}' does not exist", True
        
        # Get row count
        row_count = get_row_count(src_conn, src_table)
        if row_count == 0:
            return 0, f"[SKIP] 0 rows in '{src_table}'", True
        
        # Get available columns in source
        available_cols = get_table_columns(src_conn, src_table)
        
        # Build SELECT columns (only include columns that exist)
        select_cols = []
        for src_col in col_map.keys():
            if src_col in available_cols:
                select_cols.append(src_col)
        
        if not select_cols:
            return 0, f"[ERROR] No valid columns found in '{src_table}'", False
        
        # Get target columns for INSERT
        target_cols = [col_map[src_col] for src_col in select_cols]
        
        # Add extra columns (like breaker_class)
        for col_name, col_spec in extra_cols.items():
            target_cols.append(col_name)
        
        # Fetch data in batches
        total_inserted = 0
        batch_num = 0
        offset = 0
        
        with src_conn.cursor() as src_cur:
            while True:
                # Fetch batch
                select_sql = sql.SQL("SELECT {} FROM {} ORDER BY {} LIMIT %s OFFSET %s").format(
                    sql.SQL(", ").join(sql.Identifier(col) for col in select_cols),
                    sql.Identifier(src_table),
                    sql.Identifier(select_cols[0])  # Use first column for deterministic ordering
                )
                src_cur.execute(select_sql, (BATCH_SIZE, offset))
                rows = src_cur.fetchall()
                
                if not rows:
                    break
                
                # Transform rows: add extra columns
                transformed_rows = []
                for row in rows:
                    row_list = list(row)
                    
                    # Handle extra columns
                    if "breaker_class" in extra_cols:
                        # Get style_id value (should be second column in tcc_tmt_frames: breaker_style_id)
                        # In source it's the 'style_id' column which is at index 1 in select_cols
                        style_id_idx = select_cols.index("style_id") if "style_id" in select_cols else None
                        if style_id_idx is not None:
                            style_id = row_list[style_id_idx]
                            breaker_class = breaker_class_lookup.get(style_id, "mccb")
                            row_list.append(breaker_class)
                        else:
                            row_list.append("mccb")
                    
                    transformed_rows.append(tuple(row_list))
                
                # Prepare INSERT statement
                insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING").format(
                    sql.Identifier(tgt_table),
                    sql.SQL(", ").join(sql.Identifier(col) for col in target_cols)
                )
                
                # Batch insert
                with tgt_conn.cursor() as tgt_cur:
                    execute_values(tgt_cur, insert_sql, transformed_rows, page_size=1000)
                
                tgt_conn.commit()
                
                total_inserted += len(rows)
                batch_num += 1
                offset += BATCH_SIZE
                
                if len(rows) < BATCH_SIZE:
                    break
        
        # Reset sequence if table has an id column
        try:
            with tgt_conn.cursor() as cur:
                cur.execute(sql.SQL(
                    "SELECT setval(pg_get_serial_sequence('{}', 'id'), "
                    "(SELECT MAX(id) FROM {}) + 1)"
                ).format(sql.Identifier(tgt_table), sql.Identifier(tgt_table)))
            tgt_conn.commit()
        except psycopg2.Error:
            pass  # Sequence may not exist or table may not have serial id
        
        return total_inserted, f"[OK] {total_inserted:,} rows", True
    
    except Exception as e:
        tgt_conn.rollback()
        return 0, f"[ERROR] {str(e)}", False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main migration function."""
    print("\n" + "="*70)
    print("TCC v5 Data Transfer Script")
    print("="*70)
    
    # Get connections
    target_dsn = get_target_dsn()
    
    print("\nConnecting to source database...")
    src_conn = connect_db(SOURCE_DSN)
    print("Connected to source: OK")
    
    print("Connecting to target database...")
    tgt_conn = connect_db(target_dsn)
    print("Connected to target: OK")
    
    try:
        # Build breaker_class lookup
        print("\nPreparing breaker_class lookup...")
        breaker_class_lookup = build_breaker_class_lookup(src_conn)
        print(f"Lookup complete: {len(breaker_class_lookup)} breaker styles found")
        
        # Transfer tables
        print("\n" + "="*70)
        print("Starting data transfer...")
        print("="*70 + "\n")
        
        start_time = time.time()
        total_rows = 0
        failed_tables = []
        
        for idx, table_config in enumerate(TABLES, 1):
            table_start = time.time()
            rows, status, success = transfer_table(
                src_conn, tgt_conn, table_config, breaker_class_lookup
            )
            elapsed = time.time() - table_start
            
            total_rows += rows
            
            # Format status line
            src_name = table_config["source"]
            tgt_name = table_config["target"]
            status_indicator = "✓" if success else "✗"
            print(f"[{idx:2d}/{len(TABLES)}] {status_indicator} {src_name:40s} -> {tgt_name:35s} {status:30s} ({elapsed:.2f}s)")
            
            if not success:
                failed_tables.append((src_name, tgt_name, status))
        
        elapsed_total = time.time() - start_time
        
        # Summary
        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"Total rows transferred: {total_rows:,}")
        print(f"Total tables: {len(TABLES)}")
        print(f"Failed tables: {len(failed_tables)}")
        print(f"Total time: {elapsed_total:.2f} seconds ({elapsed_total/60:.2f} minutes)")
        
        if failed_tables:
            print("\nFailed tables:")
            for src, tgt, err in failed_tables:
                print(f"  - {src} -> {tgt}: {err}")
        
        print("\n" + "="*70)
        if failed_tables:
            print("STATUS: COMPLETED WITH ERRORS")
        else:
            print("STATUS: SUCCESS")
        print("="*70 + "\n")
        
        return 0 if not failed_tables else 1
    
    finally:
        src_conn.close()
        tgt_conn.close()


if __name__ == "__main__":
    sys.exit(main())
