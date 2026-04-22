import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


tgt = psycopg2.connect(require_env("DATABASE_URL"))
cur = tgt.cursor()

# Check constraints on tcc_tmt_thermal_adj
cur.execute("""
    SELECT conname, contype, pg_get_constraintdef(c.oid)
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'tcc_tmt_thermal_adj'
""")
print("Target constraints:")
for r in cur.fetchall():
    print(f"  {r}")

# Check source
source_url = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL")
if not source_url:
    raise RuntimeError("Missing required environment variable: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL")

src = psycopg2.connect(source_url)
scur = src.cursor()

scur.execute("SELECT thermal_adj_id, COUNT(*) FROM breaker_tmt_thermal_adj GROUP BY thermal_adj_id HAVING COUNT(*) > 1 LIMIT 5")
print(f"\nSource duplicate IDs: {scur.fetchall()}")

scur.execute("SELECT COUNT(DISTINCT thermal_adj_id) FROM breaker_tmt_thermal_adj")
print(f"Source distinct IDs: {scur.fetchone()[0]}")

scur.execute("SELECT COUNT(*) FROM breaker_tmt_thermal_adj WHERE thermal_adj_setting IS NULL")
print(f"Source NULL adjustment: {scur.fetchone()[0]}")

# Check if there's a unique constraint being violated
scur.execute("""
    SELECT frame_size_id, thermal_adj_setting, COUNT(*)
    FROM breaker_tmt_thermal_adj
    GROUP BY frame_size_id, thermal_adj_setting
    HAVING COUNT(*) > 1
    LIMIT 5
""")
print(f"\nSource duplicate (frame_id, adjustment): {scur.fetchall()}")

# Check target column info
cur.execute("""
    SELECT column_name, is_nullable, data_type
    FROM information_schema.columns
    WHERE table_name = 'tcc_tmt_thermal_adj'
    ORDER BY ordinal_position
""")
print(f"\nTarget columns: {cur.fetchall()}")

src.close()
tgt.close()
