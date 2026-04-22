"""Tests for control-plane sync helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.control_plane.sync import load_task_packet, parse_immediate_top10


def test_load_task_packet_extracts_route_metadata(tmp_path: Path):
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(
        json.dumps(
            {
                "task_id": "2026-03-28-example-001",
                "title": "Example packet",
                "lane": "workspace-governance",
                "primary_repo": "apex-power-ops-platform",
                "status": "pending",
                "action_type": "review",
                "risk_level": "high",
                "briefing_path": "Development/Control-Plane/example.md",
                "claimed_by": "",
                "created_at": "2026-03-28T00:00:00Z",
                "last_updated_at": "2026-03-28T01:00:00Z",
                "route": {
                    "preferred_model_tier": "tier-a",
                    "review_gate": "tier-a review before completion acceptance",
                },
            }
        ),
        encoding="utf-8",
    )

    record = load_task_packet(packet_path)

    assert record.task_id == "2026-03-28-example-001"
    assert record.preferred_model_tier == "tier-a"
    assert record.review_gate == "tier-a review before completion acceptance"
    assert record.updated_at == "2026-03-28T01:00:00Z"


def test_parse_immediate_top10_reads_ranked_rows():
    markdown = """# ETT Immediate Top 10 -- Current

| Rank | Item | Lane | Current state | Exact next artifact | Operator note |
|---|---|---|---|---|---|
| 1 | MCC second image batch | image-assets production | ready now | `Development/example.md` | first bounded batch |
| 2 | CT / VT image residue cleanup packet | image-assets classification | staged next | `Development/other.md` | keep separate |

---
"""

    records = parse_immediate_top10(
        markdown,
        source_surface="Development/Control-Plane/ETT-IMMEDIATE-TOP-10-CURRENT.md",
    )

    assert len(records) == 2
    assert records[0].priority_rank == 1
    assert records[0].item_id == "mcc-second-image-batch"
    assert records[0].lane == "image-assets production"
    assert records[0].status == "ready now"
    assert "Development/example.md" in (records[0].notes or "")
    assert records[1].item_id == "ct-vt-image-residue-cleanup-packet"