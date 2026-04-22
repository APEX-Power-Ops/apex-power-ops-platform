import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("Missing required environment variable: DATABASE_URL")

conn = psycopg2.connect(database_url, connect_timeout=15)
cur = conn.cursor()
targets = [
    'tcc_brk_mccb', 'tcc_brk_mccb_styles',
    'tcc_etu_ltpu_pickups', 'tcc_etu_ltpu_multipliers',
    'tcc_etu_stpu_pickups', 'tcc_etu_inst_pickups',
    'tcc_etu_gfpu_pickups', 'tcc_etu_ltd_bands',
    'tcc_etu_std_bands', 'tcc_etu_gfd_bands',
    'tcc_etu_std_equations', 'tcc_etu_gfd_equations',
    'tcc_etu_inst_curves', 'tcc_etu_sensor_params',
    'tcc_etu_ltd_params', 'tcc_etu_stpu_overrides',
    'tcc_etu_sensor_maint', 'tcc_tmt_frames',
]
for t in targets:
    cur.execute(
        """SELECT column_name, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position""",
        (t,),
    )
    cols = [(r[0], r[1], 'default' if r[2] else '') for r in cur.fetchall()]
    print(f"\n{t}:")
    for c, n, d in cols:
        marker = 'NOT NULL' if n == 'NO' else 'nullable'
        print(f"  {c}: {marker} {d}")
conn.close()
