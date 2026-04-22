import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


source_url = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL")
if not source_url:
    raise RuntimeError("Missing required environment variable: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL")

conn = psycopg2.connect(source_url)
cur = conn.cursor()

tables = [
    "sst_stpu_settings", "sst_inst_settings", "sst_gfpu_settings",
    "sst_std_settings", "sst_gfd_settings", "sst_inst_curves",
    "sst_stpu_overrides", "sst_sensor_maintenance",
    "breaker_mccb_styles", "breaker_iccb_styles", "breaker_pcb_styles",
]
for t in tables:
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name=%s ORDER BY ordinal_position", (t,)
    )
    cols = [r[0] for r in cur.fetchall()]
    print(f"{t}: {cols}")

# Also check target
conn2 = psycopg2.connect(require_env("DATABASE_URL"))
cur2 = conn2.cursor()
target_tables = [
    "tcc_etu_stpu_pickups", "tcc_etu_inst_pickups", "tcc_etu_gfpu_pickups",
    "tcc_etu_std_bands", "tcc_etu_gfd_bands", "tcc_etu_inst_curves",
    "tcc_etu_stpu_overrides", "tcc_etu_sensor_maint",
    "tcc_brk_mccb_styles", "tcc_brk_iccb_styles", "tcc_brk_pcb_styles",
]
print("\n--- TARGET ---")
for t in target_tables:
    cur2.execute(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name=%s ORDER BY ordinal_position", (t,)
    )
    cols = [(r[0], r[1]) for r in cur2.fetchall()]
    print(f"{t}: {cols}")

conn.close()
conn2.close()
