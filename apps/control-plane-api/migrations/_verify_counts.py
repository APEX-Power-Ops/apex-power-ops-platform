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

src = psycopg2.connect(source_url)
tgt = psycopg2.connect(require_env("DATABASE_URL"))

TABLE_MAP = {
    "manufacturers": "tcc_manufacturers",
    "trip_types": "tcc_trip_types",
    "trip_styles": "tcc_trip_styles",
    "breaker_iccb": "tcc_brk_iccb",
    "breaker_iccb_styles": "tcc_brk_iccb_styles",
    "breaker_mccb": "tcc_brk_mccb",
    "breaker_mccb_styles": "tcc_brk_mccb_styles",
    "breaker_pcb": "tcc_brk_pcb",
    "breaker_pcb_styles": "tcc_brk_pcb_styles",
    "breaker_tmt_frame_sizes": "tcc_tmt_frames",
    "breaker_tmt_frame_amps": "tcc_tmt_amps",
    "breaker_tmt_frame_curves": "tcc_tmt_curves",
    "breaker_tmt_frame_settings": "tcc_tmt_settings",
    "breaker_tmt_thermal_adj": "tcc_tmt_thermal_adj",
    "emt": "tcc_emt",
    "emt_frames": "tcc_emt_frames",
    "emt_frame_amps": "tcc_emt_frame_amps",
    "emt_sections": "tcc_emt_sections",
    "emt_band_names": "tcc_emt_band_names",
    "emt_pickups": "tcc_emt_pickups",
    "emt_curves": "tcc_emt_curves",
    "sst_plugs": "tcc_etu_plugs",
    "sst_sensors": "tcc_etu_sensors",
    "sst_ltpu_settings": "tcc_etu_ltpu_pickups",
    "sst_ltpu_multipliers": "tcc_etu_ltpu_multipliers",
    "sst_stpu_settings": "tcc_etu_stpu_pickups",
    "sst_inst_settings": "tcc_etu_inst_pickups",
    "sst_gfpu_settings": "tcc_etu_gfpu_pickups",
    "sst_ltd_settings": "tcc_etu_ltd_bands",
    "sst_std_settings": "tcc_etu_std_bands",
    "sst_gfd_settings": "tcc_etu_gfd_bands",
    "sst_std_inverse_equations": "tcc_etu_std_equations",
    "sst_gfd_inverse_equations": "tcc_etu_gfd_equations",
    "sst_inst_curves": "tcc_etu_inst_curves",
    "sst_sensor_parameters": "tcc_etu_sensor_params",
    "sst_sensor_sec2_params": "tcc_etu_ltd_params",
    "sst_stpu_overrides": "tcc_etu_stpu_overrides",
    "sst_sensor_maintenance": "tcc_etu_sensor_maint",
}

src_cur = src.cursor()
tgt_cur = tgt.cursor()

total_src = 0
total_tgt = 0
mismatches = []

print(f"{'Source Table':<35} {'Target Table':<30} {'Source':>10} {'Target':>10} {'Match':>7}")
print("-" * 95)

for s, t in TABLE_MAP.items():
    src_cur.execute(f"SELECT COUNT(*) FROM {s}")
    sc = src_cur.fetchone()[0]
    tgt_cur.execute(f"SELECT COUNT(*) FROM {t}")
    tc = tgt_cur.fetchone()[0]
    total_src += sc
    total_tgt += tc
    match = "✓" if sc == tc else f"Δ {sc - tc}"
    if sc != tc:
        mismatches.append((s, t, sc, tc))
    print(f"{s:<35} {t:<30} {sc:>10,} {tc:>10,} {match:>7}")

print("-" * 95)
print(f"{'TOTAL':<35} {'':<30} {total_src:>10,} {total_tgt:>10,}   Δ {total_src - total_tgt}")

if mismatches:
    print(f"\n{len(mismatches)} table(s) with count mismatch:")
    for s, t, sc, tc in mismatches:
        print(f"  {s}: source={sc:,} target={tc:,} (diff={sc-tc:,})")
else:
    print("\n✓ ALL TABLES MATCH EXACTLY")

src.close()
tgt.close()
