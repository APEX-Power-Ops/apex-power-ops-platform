import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL")
if not database_url:
    raise RuntimeError("Missing required environment variable: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL")

conn = psycopg2.connect(database_url)
cur = conn.cursor()
tables = [
    'breaker_mccb', 'sst_ltpu_settings', 'sst_ltpu_multipliers',
    'sst_stpu_settings', 'sst_inst_settings', 'sst_gfpu_settings',
    'sst_ltd_settings', 'sst_std_settings', 'sst_gfd_settings',
    'sst_std_inverse_equations', 'sst_gfd_inverse_equations',
    'sst_inst_curves', 'sst_sensor_parameters', 'sst_sensor_sec2_params',
    'sst_stpu_overrides', 'sst_sensor_maintenance',
    'breaker_mccb_styles', 'breaker_tmt_frame_sizes',
]
for t in tables:
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position",
        (t,),
    )
    cols = [r[0] for r in cur.fetchall()]
    print(f"{t}: {cols}")
conn.close()
