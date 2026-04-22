"""
Full Access DB → Supabase Import Script
========================================
Imports all DatSensor (93 cols), DatSensorMaint (59 cols),
DatSettings (6 cols), and DatPlugs (2 cols) from Access DB CSV exports
into the expanded Supabase schema.

Run from VS Code terminal:
    pip install psycopg2-binary
    python migrations/full_access_import.py

Prerequisites:
    - Supabase migrations already applied (expand_tcc_etu_sensors_full_datsensor,
      expand_tcc_etu_sensor_maint_full_datsensormaint,
      create_tcc_etu_settings_table, fix_tcc_etu_plugs_add_sensor_id)
    - Access DB CSV exports at C:\\Users\\jjswe\\Box\\TCC_Master\\Access DB\\tables\\
"""

import csv
import os
import sys
import time
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# ─── Configuration ───────────────────────────────────────────────────────────

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    print("ERROR: Missing required environment variable: DATABASE_URL")
    sys.exit(1)

CSV_DIR = Path(r"C:\Users\jjswe\Box\TCC_Master\Access DB\tables")

# ─── Column Mappings ─────────────────────────────────────────────────────────

# DatSensor CSV header → tcc_etu_sensors column
SENSOR_COLS = [
    ("SensorID",             "id"),
    ("StyleID",              "trip_style_id"),
    ("SensorValue",          "rating"),
    ("SensorDesc",           "description"),
    ("SensorIdx",            "sensor_idx"),
    ("SEC1_NAME",            "ltpu_name"),
    ("SEC1_LTF",             "ltpu_func"),
    ("DS1_TOL_HIGH",         "ltpu_tol_hi"),
    ("DS1_TOL_LOW",          "ltpu_tol_lo"),
    ("DS1_PICKUP_CALC",      "ltpu_calc"),
    ("MUL_NAME",             "ltpu_mul_name"),
    ("DS1_STEP_SIZE",        "ltpu_step"),
    ("DS1_C_NAME",           "ltpu_c_name"),
    ("SEC2_NAME",            "ltd_name"),
    ("SETTING_METHOD",       "ltd_setting_method"),
    ("SEC2_LTF",             "ltd_func"),
    ("DS2_TOL_HIGH",         "ltd_tol_hi"),
    ("DS2_TOL_LOW",          "ltd_tol_lo"),
    ("DS2_STEP_SIZE",        "ltd_step"),
    ("SETTING_VAL",          "ltd_setting_val"),
    ("SETTING_TYPE",         "ltd_setting_type"),
    ("SLOPE",                "ltd_slope"),
    ("SEC3_NAME",            "stpu_name"),
    ("SEC3_STF",             "stpu_func"),
    ("DS3_TOL_HIGH",         "stpu_tol_hi"),
    ("DS3_TOL_LOW",          "stpu_tol_lo"),
    ("DS3_SEC3_I2T",         "stpu_i2t"),
    ("DS3_PICKUP_CALC",      "stpu_calc"),
    ("DS3_STEP_SIZE",        "stpu_step"),
    ("DS3_I2T_VAL",          "stpu_i2t_val"),
    ("DS3_I2T_TYPE",         "stpu_i2t_type"),
    ("SEC4_NAME",            "inst_name"),
    ("INST_FUNC",            "inst_func"),
    ("DS4_TOL_HIGH",         "inst_tol_hi"),
    ("DS4_TOL_LOW",          "inst_tol_lo"),
    ("DS4_STEP_SIZE",        "inst_step"),
    ("DS4_PICKUP_CALC",      "inst_calc"),
    ("DS4_OVR_CALC",         "inst_ovr_calc"),
    ("DS4_OVR_VALUE",        "inst_ovr_value"),
    ("IDELAY_OPENING",       "inst_delay_opening"),
    ("IDELAY_CLEARING",      "inst_delay_clearing"),
    ("FR_OPENING",           "frame_opening"),
    ("FR_CLOSING",           "frame_closing"),
    ("SEC1GF_NAME",          "gfpu_name"),
    ("SEC1GF_GFF",           "gfpu_func"),
    ("DS1GF_TOL_HIGH",       "gfpu_tol_hi"),
    ("DS1GF_TOL_LOW",        "gfpu_tol_lo"),
    ("DS1GF_SEC3_I2T",       "gfpu_i2t"),
    ("DS1GF_PICKUP_CALC",    "gfpu_calc"),
    ("DS1GF_STEP_SIZE",      "gfpu_step"),
    ("DS1GF_I2T_VAL",        "gfpu_i2t_val"),
    ("DS1Gf_I2T_TYPE",       "gfpu_i2t_type"),
    ("DS1Gf_PICKUP_MAX",     "gfpu_pickup_max"),
    ("DS3_STP_TRACKS",       "stpu_stp_tracks"),
    ("DS4_REQ_INST",         "inst_req_inst"),
    ("DS4_REQ_STTRIP",       "inst_req_sttrip"),
    ("DS4_OVRTOL_MIN",       "inst_ovrtol_min"),
    ("DS4_OVRTOL_MAX",       "inst_ovrtol_max"),
    ("DS3_MNMXT_MINCALC",   "stpu_mnmxt_mincalc"),
    ("DS3_MNMXT_MINVAL",    "stpu_mnmxt_minval"),
    ("DS3_MNMXT_MINUNIT",   "stpu_mnmxt_minunit"),
    ("DS3_MNMXT_MAXCALC",   "stpu_mnmxt_maxcalc"),
    ("DS3_MNMXT_MAXVAL",    "stpu_mnmxt_maxval"),
    ("DS3_MNMXT_MAXUNIT",   "stpu_mnmxt_maxunit"),
    ("DS3_MNMXT_MAXAMPS",   "stpu_mnmxt_maxamps"),
    ("DS4_MNMXI_MINCALC",   "inst_mnmxi_mincalc"),
    ("DS4_MNMXI_MINVAL",    "inst_mnmxi_minval"),
    ("DS4_MNMXI_MINUNIT",   "inst_mnmxi_minunit"),
    ("DS4_MNMXI_MAXCALC",   "inst_mnmxi_maxcalc"),
    ("DS4_MNMXI_MAXVAL",    "inst_mnmxi_maxval"),
    ("DS4_MNMXI_MAXUNIT",   "inst_mnmxi_maxunit"),
    ("DS4_MNMXI_MAXAMPS",   "inst_mnmxi_maxamps"),
    ("DS4_MNMXI_SEPSETT",   "inst_mnmxi_sepsett"),
    ("Sec4InstClrCurve",     "inst_clr_curve"),
    ("Sec4InstClrChar",      "inst_clr_char"),
    ("Sec4InstClrEnteredAt", "inst_clr_entered_at"),
    ("Sec4InstOpenCurve",    "inst_open_curve"),
    ("Sec4InstOpenChar",     "inst_open_char"),
    ("Sec4InstOpenEnteredAt","inst_open_entered_at"),
    ("Sec4InstCurveCalcClr", "inst_curve_calc_clr"),
    ("Sec4InstCurveCalcOpen","inst_curve_calc_open"),
    ("DS3_MNMXT_SEPSETT",   "stpu_mnmxt_sepsett"),
    ("DS3_MNMXT_MAXUNIT2",  "stpu_mnmxt_maxunit2"),
    ("DS3_MNMXT_ALLOWOUT",  "stpu_mnmxt_allowout"),
    ("DS4_MNMXI_ALLOWOUT",  "inst_mnmxi_allowout"),
    ("DS4_BRK_OVR",         "inst_brk_ovr"),
    ("DS2_DLY_PTY",         "ltd_dly_pty"),
    ("DS2_OPEN_MINT",       "ltd_open_mint"),
    ("DS2_CLEAR_MINT",      "ltd_clear_mint"),
    ("InclAD",              "incl_ad"),
    ("DS4_REQ_INST_CCB",    "inst_req_inst_ccb"),
    ("DS4_MNMXI_MAXUNIT2",  "inst_mnmxi_maxunit2"),
    ("DS2_ALLOW_CURVES",    "ltd_allow_curves"),
]

# DatSensorMaint CSV header → tcc_etu_sensor_maint column
MAINT_COLS = [
    ("SensorID",             "sensor_id"),
    ("SEC4_NAME",            "maint_inst_name"),
    ("INST_FUNC",            "maint_inst_func"),
    ("DS4_TOL_HIGH",         "maint_inst_tol_hi"),
    ("DS4_TOL_LOW",          "maint_inst_tol_lo"),
    ("DS4_STEP_SIZE",        "maint_inst_step"),
    ("DS4_PICKUP_CALC",      "maint_inst_calc"),
    ("DS4_OVR_CALC",         "maint_inst_ovr_calc"),
    ("DS4_OVR_VALUE",        "maint_inst_ovr_value"),
    ("IDELAY_OPENING",       "maint_inst_delay_opening"),
    ("IDELAY_CLEARING",      "maint_inst_delay_clearing"),
    ("FR_OPENING",           "maint_frame_opening"),
    ("FR_CLOSING",           "maint_frame_closing"),
    ("SEC1GF_NAME",          "maint_gfpu_name"),
    ("SEC1GF_GFF",           "maint_gfpu_func"),
    ("DS1GF_TOL_HIGH",       "maint_gfpu_tol_hi"),
    ("DS1GF_TOL_LOW",        "maint_gfpu_tol_lo"),
    ("DS1GF_SEC3_I2T",       "maint_gfpu_i2t"),
    ("DS1GF_PICKUP_CALC",    "maint_gfpu_calc"),
    ("DS1GF_STEP_SIZE",      "maint_gfpu_step"),
    ("DS1GF_I2T_VAL",        "maint_gfpu_i2t_val"),
    ("DS1Gf_I2T_TYPE",       "maint_gfpu_i2t_type"),
    ("DS1Gf_PICKUP_MAX",     "maint_gfpu_pickup_max"),
    ("DS4_REQ_INST",         "maint_inst_req_inst"),
    ("DS4_REQ_STTRIP",       "maint_inst_req_sttrip"),
    ("DS4_OVRTOL_MIN",       "maint_inst_ovrtol_min"),
    ("DS4_OVRTOL_MAX",       "maint_inst_ovrtol_max"),
    ("DS4_MNMXI_MINCALC",   "maint_inst_mnmxi_mincalc"),
    ("DS4_MNMXI_MINVAL",    "maint_inst_mnmxi_minval"),
    ("DS4_MNMXI_MINUNIT",   "maint_inst_mnmxi_minunit"),
    ("DS4_MNMXI_MAXCALC",   "maint_inst_mnmxi_maxcalc"),
    ("DS4_MNMXI_MAXVAL",    "maint_inst_mnmxi_maxval"),
    ("DS4_MNMXI_MAXUNIT",   "maint_inst_mnmxi_maxunit"),
    ("DS4_MNMXI_MAXAMPS",   "maint_inst_mnmxi_maxamps"),
    ("DS4_MNMXI_SEPSETT",   "maint_inst_mnmxi_sepsett"),
    ("Sec4InstClrCurve",     "maint_inst_clr_curve"),
    ("Sec4InstClrChar",      "maint_inst_clr_char"),
    ("Sec4InstClrEnteredAt", "maint_inst_clr_entered_at"),
    ("Sec4InstOpenCurve",    "maint_inst_open_curve"),
    ("Sec4InstOpenChar",     "maint_inst_open_char"),
    ("Sec4InstOpenEnteredAt","maint_inst_open_entered_at"),
    ("Sec4InstCurveCalcClr", "maint_inst_curve_calc_clr"),
    ("Sec4InstCurveCalcOpen","maint_inst_curve_calc_open"),
    ("DS4_MNMXI_ALLOWOUT",  "maint_inst_mnmxi_allowout"),
    ("DS4_BRK_OVR",         "maint_inst_brk_ovr"),
    ("DS4_REQ_INST_CCB",    "maint_inst_req_inst_ccb"),
    ("DS4_MNMXI_MAXUNIT2",  "maint_inst_mnmxi_maxunit2"),
    ("GIDELAY_OPENING",     "maint_gf_delay_opening"),
    ("GIDELAY_CLEARING",    "maint_gf_delay_clearing"),
    ("GFR_OPENING",         "maint_gf_frame_opening"),
    ("GFR_CLOSING",         "maint_gf_frame_closing"),
    ("SecGfInstClrCurve",    "maint_gf_inst_clr_curve"),
    ("SecGfInstClrChar",     "maint_gf_inst_clr_char"),
    ("SecGfInstClrEnteredAt","maint_gf_inst_clr_entered_at"),
    ("SecGfInstOpenCurve",   "maint_gf_inst_open_curve"),
    ("SecGfInstOpenChar",    "maint_gf_inst_open_char"),
    ("SecGfInstOpenEnteredAt","maint_gf_inst_open_entered_at"),
    ("SecGfInstCurveCalcClr","maint_gf_inst_curve_calc_clr"),
    ("SecGfInstCurveCalcOpen","maint_gf_inst_curve_calc_open"),
]

# Text columns (everything else is numeric)
TEXT_COLS = {
    "SensorDesc", "SEC1_NAME", "MUL_NAME", "DS1_C_NAME", "SEC2_NAME",
    "SEC3_NAME", "SEC4_NAME", "SEC1GF_NAME", "Description", "TextParm1",
}

# Integer columns (Access Long/Byte → integer/smallint)
INT_COLS = {
    "SensorID", "StyleID", "SensorValue", "SensorIdx",
    "SEC1_LTF", "DS1_PICKUP_CALC",
    "SETTING_METHOD", "SEC2_LTF", "SETTING_TYPE",
    "SEC3_STF", "DS3_SEC3_I2T", "DS3_PICKUP_CALC", "DS3_I2T_TYPE",
    "INST_FUNC", "DS4_PICKUP_CALC", "DS4_OVR_CALC",
    "SEC1GF_GFF", "DS1GF_SEC3_I2T", "DS1GF_PICKUP_CALC", "DS1Gf_I2T_TYPE",
    "DS3_STP_TRACKS", "DS4_REQ_INST", "DS4_REQ_STTRIP",
    "DS3_MNMXT_MINCALC", "DS3_MNMXT_MINUNIT", "DS3_MNMXT_MAXCALC", "DS3_MNMXT_MAXUNIT",
    "DS4_MNMXI_MINCALC", "DS4_MNMXI_MINUNIT", "DS4_MNMXI_MAXCALC", "DS4_MNMXI_MAXUNIT",
    "DS4_MNMXI_SEPSETT",
    "Sec4InstClrCurve", "Sec4InstClrChar", "Sec4InstOpenCurve", "Sec4InstOpenChar",
    "Sec4InstCurveCalcClr", "Sec4InstCurveCalcOpen",
    "DS3_MNMXT_SEPSETT", "DS3_MNMXT_MAXUNIT2", "DS3_MNMXT_ALLOWOUT",
    "DS4_MNMXI_ALLOWOUT", "DS4_BRK_OVR", "DS2_DLY_PTY",
    "InclAD", "DS4_REQ_INST_CCB", "DS4_MNMXI_MAXUNIT2", "DS2_ALLOW_CURVES",
    "KeyID", "Ordinal",
    "SecGfInstClrCurve", "SecGfInstClrChar", "SecGfInstOpenCurve", "SecGfInstOpenChar",
    "SecGfInstCurveCalcClr", "SecGfInstCurveCalcOpen",
    "GIDELAY_OPENING",  # actually numeric but listed for safety
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def clean_val(val, col_name):
    """Convert a CSV string to a Python value for psycopg2."""
    if val is None or val.strip() == "":
        return None
    val = val.strip()
    if col_name in TEXT_COLS:
        return val
    if col_name in INT_COLS:
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return val


def read_csv(filename):
    """Read a CSV file and return rows as list of dicts."""
    path = CSV_DIR / filename
    if not path.exists():
        print(f"  ERROR: {path} not found!")
        return []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [r for r in reader if r.get(reader.fieldnames[0], "").strip()]


def progress(current, total, label=""):
    """Print a progress bar."""
    pct = current / total * 100 if total else 0
    bar = "█" * int(pct // 2) + "░" * (50 - int(pct // 2))
    print(f"\r  {bar} {pct:5.1f}% ({current}/{total}) {label}", end="", flush=True)


# ─── Import Functions ────────────────────────────────────────────────────────

def import_sensors(conn):
    """UPSERT all 17,831 DatSensor rows → tcc_etu_sensors (93 columns)."""
    print("\n" + "=" * 60)
    print("STEP 1: DatSensor → tcc_etu_sensors (UPSERT)")
    print("=" * 60)

    rows = read_csv("DatSensor.csv")
    print(f"  Source rows: {len(rows)}")
    if not rows:
        return 0

    access_cols = [c[0] for c in SENSOR_COLS]
    pg_cols = [c[1] for c in SENSOR_COLS]

    col_list = ", ".join(pg_cols)
    placeholders = ", ".join(["%s"] * len(pg_cols))
    update_sets = ", ".join(f"{c} = EXCLUDED.{c}" for c in pg_cols if c != "id")

    sql = f"""
        INSERT INTO tcc_etu_sensors ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE SET {update_sets}
    """

    cur = conn.cursor()
    batch_size = 500
    t0 = time.time()

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        values = []
        for row in batch:
            vals = tuple(clean_val(row.get(ac, ""), ac) for ac in access_cols)
            values.append(vals)
        psycopg2.extras.execute_batch(cur, sql, values, page_size=100)
        conn.commit()
        progress(min(i + batch_size, len(rows)), len(rows))

    elapsed = time.time() - t0
    print(f"\n  Done in {elapsed:.1f}s")

    cur.execute("SELECT count(*) FROM tcc_etu_sensors")
    count = cur.fetchone()[0]
    print(f"  ✓ tcc_etu_sensors: {count} rows")
    cur.close()
    return count


def import_sensor_maint(conn):
    """UPDATE all 2,572 DatSensorMaint rows → tcc_etu_sensor_maint."""
    print("\n" + "=" * 60)
    print("STEP 2: DatSensorMaint → tcc_etu_sensor_maint (UPDATE)")
    print("=" * 60)

    rows = read_csv("DatSensorMaint.csv")
    print(f"  Source rows: {len(rows)}")
    if not rows:
        return 0

    # Build UPDATE for all new maint columns (skip sensor_id which is the WHERE key)
    new_cols = [(ac, pg) for ac, pg in MAINT_COLS if pg != "sensor_id"]
    set_clause = ", ".join(f"{pg} = %s" for _, pg in new_cols)
    sql = f"UPDATE tcc_etu_sensor_maint SET {set_clause} WHERE sensor_id = %s"

    cur = conn.cursor()
    updated = 0
    not_found = 0
    t0 = time.time()

    for idx, row in enumerate(rows):
        sensor_id = int(row["SensorID"])
        vals = [clean_val(row.get(ac, ""), ac) for ac, _ in new_cols]
        vals.append(sensor_id)
        cur.execute(sql, tuple(vals))
        if cur.rowcount > 0:
            updated += 1
        else:
            not_found += 1
        if (idx + 1) % 100 == 0:
            progress(idx + 1, len(rows))

    conn.commit()
    elapsed = time.time() - t0
    print(f"\n  Done in {elapsed:.1f}s")
    print(f"  ✓ Updated: {updated}, Not found in Supabase: {not_found}")
    cur.close()
    return updated


def import_settings(conn):
    """INSERT all 3,514 DatSettings rows → tcc_etu_settings."""
    print("\n" + "=" * 60)
    print("STEP 3: DatSettings → tcc_etu_settings (UPSERT)")
    print("=" * 60)

    rows = read_csv("DatSettings.csv")
    print(f"  Source rows: {len(rows)}")
    if not rows:
        return 0

    sql = """
        INSERT INTO tcc_etu_settings (id, sensor_id, ordinal, description, setting, text_parm1)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            sensor_id = EXCLUDED.sensor_id,
            ordinal = EXCLUDED.ordinal,
            description = EXCLUDED.description,
            setting = EXCLUDED.setting,
            text_parm1 = EXCLUDED.text_parm1
    """

    cur = conn.cursor()
    values = []
    t0 = time.time()

    for row in rows:
        key_id = clean_val(row.get("KeyID", ""), "KeyID")
        sensor_id = clean_val(row.get("SensorID", ""), "SensorID")
        ordinal = clean_val(row.get("Ordinal", ""), "Ordinal")
        desc = clean_val(row.get("Description", ""), "Description")
        setting = clean_val(row.get("Setting", ""), "Setting")
        text = clean_val(row.get("TextParm1", ""), "TextParm1")
        values.append((key_id, sensor_id, ordinal, desc, setting, text))

    psycopg2.extras.execute_batch(cur, sql, values, page_size=200)
    conn.commit()
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s")

    cur.execute("SELECT count(*) FROM tcc_etu_settings")
    count = cur.fetchone()[0]
    print(f"  ✓ tcc_etu_settings: {count} rows")
    cur.close()
    return count


def import_plugs(conn):
    """TRUNCATE and re-INSERT all 49,901 DatPlugs rows with correct sensor_id FK."""
    print("\n" + "=" * 60)
    print("STEP 4: DatPlugs → tcc_etu_plugs (TRUNCATE + INSERT)")
    print("=" * 60)

    rows = read_csv("DatPlugs.csv")
    print(f"  Source rows: {len(rows)}")
    if not rows:
        return 0

    cur = conn.cursor()

    # Get sensor_id → trip_style_id mapping
    cur.execute("SELECT id, trip_style_id FROM tcc_etu_sensors")
    sensor_style = {r[0]: r[1] for r in cur.fetchall()}
    print(f"  Sensor→Style lookup: {len(sensor_style)} entries")

    # Truncate existing
    cur.execute("SELECT count(*) FROM tcc_etu_plugs")
    existing = cur.fetchone()[0]
    print(f"  Existing plugs: {existing} (will truncate)")
    cur.execute("TRUNCATE TABLE tcc_etu_plugs RESTART IDENTITY")
    conn.commit()

    sql = "INSERT INTO tcc_etu_plugs (sensor_id, trip_style_id, value) VALUES (%s, %s, %s)"

    values = []
    skipped = 0
    t0 = time.time()

    for row in rows:
        sid_raw = row.get("SensorID", "").strip()
        pv_raw = row.get("PlugVal", "").strip()
        if not sid_raw or not pv_raw:
            skipped += 1
            continue
        sensor_id = int(sid_raw)
        plug_val = int(pv_raw)
        style_id = sensor_style.get(sensor_id)
        values.append((sensor_id, style_id, plug_val))

    batch_size = 2000
    for i in range(0, len(values), batch_size):
        batch = values[i:i + batch_size]
        psycopg2.extras.execute_batch(cur, sql, batch, page_size=200)
        conn.commit()
        progress(min(i + batch_size, len(values)), len(values))

    elapsed = time.time() - t0
    print(f"\n  Done in {elapsed:.1f}s")

    cur.execute("SELECT count(*) FROM tcc_etu_plugs")
    count = cur.fetchone()[0]
    print(f"  ✓ tcc_etu_plugs: {count} rows (was {existing})")
    if skipped:
        print(f"  Skipped {skipped} rows with null values")
    cur.close()
    return count


# ─── Verification ────────────────────────────────────────────────────────────

def verify(conn):
    """Post-import data integrity checks."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    cur = conn.cursor()

    # Row counts
    expected = {
        "tcc_etu_sensors": 17831,
        "tcc_etu_sensor_maint": 2572,
        "tcc_etu_settings": 3514,
        "tcc_etu_plugs": 49901,
    }

    print("\n  Row Counts:")
    all_match = True
    for table, exp in expected.items():
        cur.execute(f"SELECT count(*) FROM {table}")
        actual = cur.fetchone()[0]
        status = "✓" if actual == exp else "✗"
        if actual != exp:
            all_match = False
        print(f"    {status} {table}: {actual} (expected {exp})")

    # New columns populated
    print("\n  New Column Coverage (tcc_etu_sensors):")
    checks = [
        ("ltd_tol_hi", "LTD sensor-level tolerance"),
        ("ltpu_func", "LTPU continuous flag"),
        ("stpu_func", "STPU continuous flag"),
        ("inst_func", "INST continuous flag"),
        ("gfpu_func", "GF continuous flag"),
        ("inst_delay_opening", "INST delay opening"),
        ("ltd_setting_method", "LTD setting method"),
        ("sensor_idx", "Sensor index"),
    ]
    for col, label in checks:
        cur.execute(f"SELECT count(*) FILTER (WHERE {col} IS NOT NULL) FROM tcc_etu_sensors")
        populated = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM tcc_etu_sensors")
        total = cur.fetchone()[0]
        pct = populated / total * 100 if total else 0
        print(f"    {col}: {populated}/{total} ({pct:.0f}%) — {label}")

    # LTD tolerance distribution (should NOT all be ±10)
    print("\n  LTD Tolerance Distribution (top 10):")
    cur.execute("""
        SELECT ltd_tol_hi, ltd_tol_lo, count(*) as cnt
        FROM tcc_etu_sensors
        WHERE ltd_tol_hi IS NOT NULL
        GROUP BY ltd_tol_hi, ltd_tol_lo
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"    +{row[0]}/-{row[1]}: {row[2]} sensors")

    # GFPU tolerance check (should now have real per-sensor values)
    print("\n  GFPU Tolerance Distribution (top 10):")
    cur.execute("""
        SELECT gfpu_tol_hi, gfpu_tol_lo, count(*) as cnt
        FROM tcc_etu_sensors
        WHERE gfpu_tol_hi IS NOT NULL
        GROUP BY gfpu_tol_hi, gfpu_tol_lo
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"    +{row[0]}/-{row[1]}: {row[2]} sensors")

    # Plugs FK check — any orphans?
    print("\n  FK Integrity:")
    cur.execute("""
        SELECT count(*) FROM tcc_etu_plugs p
        WHERE NOT EXISTS (SELECT 1 FROM tcc_etu_sensors s WHERE s.id = p.sensor_id)
    """)
    orphan_plugs = cur.fetchone()[0]
    print(f"    Plugs orphans (no matching sensor): {orphan_plugs}")

    cur.execute("""
        SELECT count(*) FROM tcc_etu_settings st
        WHERE NOT EXISTS (SELECT 1 FROM tcc_etu_sensors s WHERE s.id = st.sensor_id)
    """)
    orphan_settings = cur.fetchone()[0]
    print(f"    Settings orphans (no matching sensor): {orphan_settings}")

    # Sample sensor check
    print("\n  Sample Sensor (id=1):")
    cur.execute("""
        SELECT id, rating, ltpu_tol_hi, ltpu_tol_lo, ltd_tol_hi, ltd_tol_lo,
               stpu_tol_hi, stpu_tol_lo, inst_tol_hi, inst_tol_lo,
               gfpu_tol_hi, gfpu_tol_lo,
               ltpu_func, stpu_func, inst_func, gfpu_func,
               ltd_setting_method, ltd_slope
        FROM tcc_etu_sensors WHERE id = 1
    """)
    row = cur.fetchone()
    if row:
        print(f"    Rating: {row[1]}")
        print(f"    LTPU tol: +{row[2]}/-{row[3]}")
        print(f"    LTD tol:  +{row[4]}/-{row[5]}")
        print(f"    STPU tol: +{row[6]}/-{row[7]}")
        print(f"    INST tol: +{row[8]}/-{row[9]}")
        print(f"    GFPU tol: +{row[10]}/-{row[11]}")
        print(f"    Funcs: LTPU={row[12]} STPU={row[13]} INST={row[14]} GFPU={row[15]}")
        print(f"    LTD method={row[16]}, slope={row[17]}")

    cur.close()
    return all_match


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  TCC Access DB → Supabase Full Import                   ║")
    print("║  Phase 2: ETU/DAT Family Completion                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Verify CSV directory
    if not CSV_DIR.exists():
        print(f"ERROR: CSV directory not found: {CSV_DIR}")
        sys.exit(1)

    csv_files = ["DatSensor.csv", "DatSensorMaint.csv", "DatSettings.csv", "DatPlugs.csv"]
    for f in csv_files:
        path = CSV_DIR / f
        if path.exists():
            with open(path) as fh:
                count = sum(1 for _ in fh) - 1
            print(f"  ✓ {f}: {count} rows")
        else:
            print(f"  ✗ {f}: NOT FOUND")
            sys.exit(1)

    print(f"\n  Connecting to Supabase...")
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=10)
        print(f"  ✓ Connected")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        sys.exit(1)

    try:
        import_sensors(conn)
        import_sensor_maint(conn)
        import_settings(conn)
        import_plugs(conn)

        all_good = verify(conn)

        print("\n" + "=" * 60)
        if all_good:
            print("✓ IMPORT COMPLETE — All row counts match!")
        else:
            print("⚠ IMPORT COMPLETE — Some row counts differ, check above")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
