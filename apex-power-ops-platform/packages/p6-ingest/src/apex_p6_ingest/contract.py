from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[3]
DEFAULT_FIXTURE_PATH = REPO_ROOT / "apps" / "mutation-seam" / "app" / "schedule" / "fixtures" / "stack_data_center_baseline_sanitized.xer"
DEFAULT_ARTIFACTS_PATH = Path("/var/lib/p6-ingest/artifacts")

_FIXTURE_SUMMARY_JSON = """{
  "baseline_entry": {
    "baseline_name": "Stack DC \u2014 Original Baseline R01",
    "baseline_source": "p6_import",
    "matched_schedule_task_ids": [
      "sched-task-7001",
      "sched-task-7002",
      "sched-task-7003"
    ],
    "matched_task_codes": [
      "A10",
      "A20",
      "A30"
    ],
    "matched_task_dates": {
      "A10": {
        "baseline_finish": "2026-04-28 17:00",
        "baseline_start": "2026-04-27 07:00"
      },
      "A20": {
        "baseline_finish": "2026-05-01 17:00",
        "baseline_start": "2026-04-29 07:00"
      },
      "A30": {
        "baseline_finish": "2026-05-08 17:00",
        "baseline_start": "2026-05-04 07:00"
      }
    },
    "p6_baseline_proj_id": "9998",
    "schedule_project_id": "sched-proj-1001"
  },
  "baseline_row": {
    "base_proj_id": "9998",
    "base_type_name": "Stack DC \u2014 Original Baseline R01",
    "count": 1,
    "last_update_date": "2026-02-01 00:00",
    "proj_id": "1001"
  },
  "fixture": "stack_data_center_baseline_sanitized.xer",
  "live_lane": {
    "project_ids": [
      "1001"
    ],
    "relationship_count": 1,
    "task_codes": [
      "A10",
      "A20",
      "A30",
      "A99"
    ],
    "wbs_count": 1
  },
  "negative_cases": {
    "baseline_only_a90_absent_from_live_lane": true,
    "live_only_a99_present": true
  },
  "sections": [
    "PROJBASELINE",
    "PROJECT",
    "PROJWBS",
    "TASK",
    "TASKPRED"
  ],
  "source_file": "stack_data_center_baseline_sanitized.xer"
}"""


def _resolve_fixture_path() -> Path:
    raw_path = os.getenv("APEX_P6_FIXTURE_PATH")
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return DEFAULT_FIXTURE_PATH.resolve()


def _resolve_artifacts_path() -> Path:
    raw_path = os.getenv("P6_INGEST_ARTIFACTS_PATH")
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return DEFAULT_ARTIFACTS_PATH


def _runtime_port() -> int:
    raw_port = os.getenv("APEX_P6_RUNTIME_PORT") or os.getenv("PORT") or "8081"
    return int(raw_port)


def get_fixture_summary() -> dict[str, Any]:
    return json.loads(_FIXTURE_SUMMARY_JSON)


def get_runtime_status() -> dict[str, Any]:
    fixture_path = _resolve_fixture_path()
    artifacts_path = _resolve_artifacts_path()
    return {
        "service": "p6-ingest",
        "status": "ok",
        "env": os.getenv("APEX_RUN_ENV", "sandbox"),
        "port": _runtime_port(),
        "fixturePath": str(fixture_path).replace("\\", "/"),
        "fixtureExists": fixture_path.exists(),
        "artifactsPath": str(artifacts_path).replace("\\", "/"),
        "artifactsPathExists": artifacts_path.exists(),
        "storage": {
            "xerBucket": os.getenv("P6_INGEST_XER_BUCKET", "p6-ingest-xer"),
            "xerPrefix": os.getenv("P6_INGEST_XER_PREFIX", "incoming"),
        },
        "oidc": {
            "issuerUrl": os.getenv("OIDC_ISSUER_URL", "https://auth.olares.local"),
            "clientId": os.getenv("OIDC_CLIENT_ID", "p6-ingest-placeholder"),
        },
    }
