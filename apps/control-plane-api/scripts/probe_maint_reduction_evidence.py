from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import engine


COUNTS_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE maint_ltpu_reduction IS NOT NULL) AS ltpu_non_null,
    COUNT(*) FILTER (WHERE maint_stpu_reduction IS NOT NULL) AS stpu_non_null,
    COUNT(*) FILTER (
        WHERE maint_ltpu_reduction IS NOT NULL
          AND maint_stpu_reduction IS NOT NULL
    ) AS both_non_null,
    COUNT(*) FILTER (WHERE maint_available IS TRUE) AS maint_available_true,
    COUNT(*) FILTER (
        WHERE POSITION('ltpu_reduction' IN COALESCE(params_json::text, '')) > 0
    ) AS params_has_ltpu_key,
    COUNT(*) FILTER (
        WHERE POSITION('stpu_reduction' IN COALESCE(params_json::text, '')) > 0
    ) AS params_has_stpu_key,
    COUNT(*) FILTER (
        WHERE POSITION('reduction' IN COALESCE(params_json::text, '')) > 0
    ) AS params_has_any_reduction_text
FROM tcc_etu_sensor_maint
"""


SAMPLE_SQL = """
SELECT
    id,
    sensor_id,
    maint_available,
    maint_ltpu_reduction,
    maint_stpu_reduction,
    params_json::text AS params_json
FROM tcc_etu_sensor_maint
WHERE maint_ltpu_reduction IS NOT NULL
   OR maint_stpu_reduction IS NOT NULL
   OR POSITION('reduction' IN COALESCE(params_json::text, '')) > 0
ORDER BY id
LIMIT 10
"""


def main() -> None:
    with engine.connect() as connection:
        counts = dict(connection.execute(text(COUNTS_SQL)).mappings().one())
        samples = [
            dict(row)
            for row in connection.execute(text(SAMPLE_SQL)).mappings().all()
        ]

    print(json.dumps({"counts": counts, "samples": samples}, default=str, indent=2))


if __name__ == "__main__":
    main()