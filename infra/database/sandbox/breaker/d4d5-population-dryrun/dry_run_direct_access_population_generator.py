"""
dry_run_direct_access_population — GENERATOR (Path B, dry-run only).

Reads the FROZEN, hash-recorded copy of D:\TCC_NEW.accdb read-only (pyodbc) and emits:
  1) dry_run_direct_access_population.sql  -- guarded population SQL (refuses unless current_database() ~ '%dryrun%')
  2) dry_run_fidelity_report.json          -- counts / nulls / PCB rating-only / spot-checks

NOT prod population. Target = a disposable sandbox clone only. Governed custody (Path A) stays the prod standard.
"""
import pyodbc, json, datetime, decimal, hashlib, os, sys

# Paths are parameterized so the committed artifact reproduces from any checkout (Codex review-9034125e):
#   DRYRUN_FROZEN_ACCDB (or argv[1]) = the FROZEN, hash-recorded .accdb copy (required; a live non-frozen read is not allowed)
#   DRYRUN_OUT_DIR      (or argv[2]) = output dir (default: a _dryrun_out/ beside this script)
HERE    = os.path.dirname(os.path.abspath(__file__))
FROZEN  = os.environ.get("DRYRUN_FROZEN_ACCDB") or (sys.argv[1] if len(sys.argv) > 1 else "")
OUT_DIR = os.environ.get("DRYRUN_OUT_DIR") or (sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "_dryrun_out"))
if not FROZEN or not os.path.isfile(FROZEN):
    sys.exit("Set DRYRUN_FROZEN_ACCDB=<frozen .accdb copy> (or pass argv[1]); a direct live-file read is not "
             "allowed for this dry-run. Got: %r" % FROZEN)
os.makedirs(OUT_DIR, exist_ok=True)
OUT_SQL = os.path.join(OUT_DIR, "dry_run_direct_access_population.sql")
OUT_RPT = os.path.join(OUT_DIR, "dry_run_fidelity_report.json")

# (breaker_class, access_table, pg_table, has_d4)
CLASSES = [
    ("ICCB", "BreakerICCBStyles", "brk_iccb_styles", True),
    ("MCCB", "BreakerMCCBStyles", "brk_mccb_styles", True),
    ("PCB",  "BreakerPCBStyles",  "brk_pcb_styles",  False),
]
# (pg_col, access_col, pg_type)
D4 = [
    ("tmt_tcc_number",       "TMT_TCCNumber",       "text"),
    ("tmt_notes",            "TMT_Notes",           "text"),
    ("tmt_trip_plug",        "TMT_TripPlug",        "smallint"),
    ("tmt_breaker_type",     "TMT_BreakerType",     "smallint"),
    ("tmt_thermal_magnetic", "TMT_ThermalMagnetic", "smallint"),
    ("tmt_thermal",          "TMT_Thermal",         "smallint"),
]
# D5 JSONB blocks keyed by verbatim Access column-name prefix
BLOCK_PREFIX = [
    ("inst_override",  lambda c: c.startswith("InstOvr")),
    ("ninst_override", lambda c: c.startswith("NInstOvr")),
    ("brk_times",      lambda c: c.startswith("BrkTimes")),
    ("r_int",          lambda c: c.startswith("r_int_")),
    ("r_iec",          lambda c: c.startswith("r_iec_")),
]
CHUNK = 500

def jdefault(o):
    if isinstance(o, decimal.Decimal): return float(o)
    if isinstance(o, (bytes, bytearray)): return o.hex()
    if isinstance(o, (datetime.datetime, datetime.date, datetime.time)): return o.isoformat()
    return str(o)

def sql_text(s):  return "'" + str(s).replace("'", "''") + "'"
def lit_text(v):  return "NULL" if v is None else sql_text(v)
def lit_int(v):   return "NULL" if v is None else str(int(v))
def sql_jsonb(d): return "NULL" if not d else sql_text(json.dumps(d, default=jdefault, ensure_ascii=False)) + "::jsonb"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

cs = r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + FROZEN + ";Mode=Read"
cx = pyodbc.connect(cs, readonly=True)
cur = cx.cursor()

sql_parts = []
report = {
    "artifact": "dry_run_direct_access_population",
    "kind": "DRY-RUN (Path B) — population-logic fidelity only, NOT prod custody",
    "frozen_source": {"path": FROZEN, "sha256": sha256(FROZEN), "size": os.path.getsize(FROZEN)},
    "classes": {},
}

for cls, atbl, ptbl, has_d4 in CLASSES:
    cur.execute("SELECT * FROM [%s]" % atbl)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    d4_rows = []        # (source_id, *d4 literals) for styles with >=1 non-null D4
    d4_nonnull = {pg: 0 for pg, _, _ in D4}
    d5_rows = []        # (cls, source_id, inst, ninst, brk, rint, riec)
    block_present = {b: 0 for b, _ in BLOCK_PREFIX}
    real_override = 0   # InstOvrAmps > 0 = the real instantaneous-override signal (NOT block non-nullness)
    rating_only = 0     # no real override but interrupt ratings present -> retained under policy (a)
    samples = []

    for row in rows:
        sid = row["ID"]
        # D4 (ICCB/MCCB only)
        d4vals = {}
        if has_d4:
            for pg, acc, _ in D4:
                v = row.get(acc)
                d4vals[pg] = v
                if v is not None:
                    d4_nonnull[pg] += 1
            if any(v is not None for v in d4vals.values()):
                d4_rows.append((sid, d4vals))
        # D5 blocks
        blocks = {}
        for bname, pred in BLOCK_PREFIX:
            blk = {c: row[c] for c in cols if pred(c) and row[c] is not None}
            blocks[bname] = blk if blk else None
            if blk:
                block_present[bname] += 1
        # Real-override discriminator: InstOvrAmps>0, NOT block non-nullness (Codex review-9034125e).
        inst_amps = row.get("InstOvrAmps")
        is_real_override = inst_amps is not None and inst_amps > 0
        has_rating = blocks["r_int"] is not None or blocks["r_iec"] is not None
        if is_real_override:
            real_override += 1
        elif has_rating:
            rating_only += 1
        if any(blocks[b] is not None for b, _ in BLOCK_PREFIX):
            d5_rows.append((sid, blocks))
            if len(samples) < 3:
                samples.append({
                    "source_id": sid,
                    "d4": {pg: d4vals.get(pg) for pg, _, _ in D4} if has_d4 else None,
                    "d5_blocks_present": [b for b, _ in BLOCK_PREFIX if blocks[b] is not None],
                    "inst_override_keys": list(blocks["inst_override"].keys()) if blocks["inst_override"] else [],
                    "r_int": blocks["r_int"],
                })

    # ---- emit D4 UPDATE chunks ----
    if has_d4 and d4_rows:
        sql_parts.append("-- D4 UPDATE: %s (%d styles with >=1 non-null helper)" % (ptbl, len(d4_rows)))
        for i in range(0, len(d4_rows), CHUNK):
            vals = []
            for sid, d in d4_rows[i:i + CHUNK]:
                vals.append("(%s,%s,%s,%s,%s,%s,%s)" % (
                    int(sid), lit_text(d["tmt_tcc_number"]), lit_text(d["tmt_notes"]),
                    lit_int(d["tmt_trip_plug"]), lit_int(d["tmt_breaker_type"]),
                    lit_int(d["tmt_thermal_magnetic"]), lit_int(d["tmt_thermal"])))
            sql_parts.append(
                "UPDATE tcc.%s s SET tmt_tcc_number=v.c1::text, tmt_notes=v.c2::text, "
                "tmt_trip_plug=v.c3::smallint, tmt_breaker_type=v.c4::smallint, "
                "tmt_thermal_magnetic=v.c5::smallint, tmt_thermal=v.c6::smallint\n"
                "FROM (VALUES %s) AS v(source_id,c1,c2,c3,c4,c5,c6) "
                "WHERE s.source_id=v.source_id::integer;" % (ptbl, ",".join(vals)))

    # ---- emit D5 INSERT chunks ----
    if d5_rows:
        sql_parts.append("-- D5 INSERT: %s -> brk_style_native_overrides (%d styles with >=1 non-null block)" % (cls, len(d5_rows)))
        for i in range(0, len(d5_rows), CHUNK):
            vals = []
            for sid, b in d5_rows[i:i + CHUNK]:
                vals.append("('%s',%d,%s,%s,%s,%s,%s,NULL)" % (
                    cls, int(sid), sql_jsonb(b["inst_override"]), sql_jsonb(b["ninst_override"]),
                    sql_jsonb(b["brk_times"]), sql_jsonb(b["r_int"]), sql_jsonb(b["r_iec"])))
            sql_parts.append(
                "INSERT INTO tcc.brk_style_native_overrides "
                "(breaker_class,source_id,inst_override,ninst_override,brk_times,r_int,r_iec,ovr_curves) "
                "VALUES %s;" % ",".join(vals))

    report["classes"][cls] = {
        "access_table": atbl, "pg_table": ptbl, "total_styles": len(rows),
        "d4_update_count": len(d4_rows) if has_d4 else 0,
        "d4_nonnull_per_col": d4_nonnull if has_d4 else None,
        "d5_insert_count": len(d5_rows),
        "d5_block_present_counts": block_present,
        "real_override_count": real_override,   # InstOvrAmps > 0
        "rating_only_count": rating_only,        # no real override but ratings present (must be retained)
        "ovr_curves_note": "always NULL (Breaker_OvrCurves empty in Access per G1; not read this dry-run)",
        "samples": samples,
    }

cx.close()

guard = (
    "-- dry_run_direct_access_population.sql  (Path B, DRY-RUN ONLY — NOT prod population)\n"
    "-- Source: FROZEN copy of D:\\TCC_NEW.accdb sha256=%s\n"
    "-- Target: a disposable *dryrun* sandbox clone ONLY. Governed custody (Path A) stays the prod standard.\n"
    "SET client_encoding='UTF8';\nSET standard_conforming_strings=on;\n"
    "DO $guard$ BEGIN\n"
    "  IF current_database() NOT LIKE '%%dryrun%%' THEN\n"
    "    RAISE EXCEPTION 'dry_run_direct_access_population REFUSES: current_database()=%% is not a *dryrun* sandbox clone', current_database();\n"
    "  END IF;\nEND $guard$;\nBEGIN;\n" % report["frozen_source"]["sha256"]
)
with open(OUT_SQL, "w", encoding="utf-8") as f:
    f.write(guard)
    f.write("\n".join(sql_parts))
    f.write("\nCOMMIT;\n")
with open(OUT_RPT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, default=jdefault)

print("SQL bytes:", os.path.getsize(OUT_SQL), "| statements:", len(sql_parts))
for cls in report["classes"]:
    c = report["classes"][cls]
    print("\n[%s] styles=%d  D4_updates=%s  D5_inserts=%d  real_override=%d  rating_only=%d"
          % (cls, c["total_styles"], c["d4_update_count"], c["d5_insert_count"], c["real_override_count"], c["rating_only_count"]))
    print("   D5 blocks present:", c["d5_block_present_counts"])
    if c["d4_nonnull_per_col"]:
        print("   D4 non-null/col:", c["d4_nonnull_per_col"])
