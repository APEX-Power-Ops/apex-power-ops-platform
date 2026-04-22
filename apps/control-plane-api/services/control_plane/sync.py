"""Helpers for syncing governed workspace surfaces into control-plane tables."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


_TOP10_HEADER = "| Rank | Item | Lane | Current state | Exact next artifact | Operator note |"


@dataclass(frozen=True)
class TaskPacketRecord:
    task_id: str
    title: str
    lane: str
    primary_repo: str
    status: str
    action_type: str
    risk_level: str
    preferred_model_tier: str | None
    review_gate: str | None
    briefing_path: str | None
    claimed_by: str | None
    created_at: str | None
    updated_at: str | None
    packet_json: dict[str, Any]


@dataclass(frozen=True)
class LanePriorityRecord:
    lane: str
    priority_rank: int
    item_id: str
    title: str
    status: str
    source_surface: str
    notes: str | None


def _normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _slugify(value: str) -> str:
    normalized = re.sub(r"`", "", value.strip().lower())
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-") or "item"


def load_task_packet(path: Path) -> TaskPacketRecord:
    payload = json.loads(path.read_text(encoding="utf-8"))
    route = payload.get("route") or {}
    return TaskPacketRecord(
        task_id=str(payload["task_id"]),
        title=str(payload["title"]),
        lane=str(payload["lane"]),
        primary_repo=str(payload["primary_repo"]),
        status=str(payload["status"]),
        action_type=str(payload["action_type"]),
        risk_level=str(payload["risk_level"]),
        preferred_model_tier=_normalize_string(route.get("preferred_model_tier")),
        review_gate=_normalize_string(route.get("review_gate")),
        briefing_path=_normalize_string(payload.get("briefing_path")),
        claimed_by=_normalize_string(payload.get("claimed_by")),
        created_at=_normalize_string(payload.get("created_at")),
        updated_at=_normalize_string(payload.get("last_updated_at")) or _normalize_string(payload.get("created_at")),
        packet_json=payload,
    )


def discover_task_packets(inbox_path: Path) -> list[TaskPacketRecord]:
    return [load_task_packet(path) for path in sorted(inbox_path.glob("*.json"))]


def parse_immediate_top10(markdown_text: str, source_surface: str) -> list[LanePriorityRecord]:
    lines = markdown_text.splitlines()
    try:
        start_index = lines.index(_TOP10_HEADER)
    except ValueError as exc:
        raise ValueError("Immediate Top 10 table header not found") from exc

    records: list[LanePriorityRecord] = []
    for raw_line in lines[start_index + 2 :]:
        if not raw_line.startswith("|"):
            break
        cells = [cell.strip() for cell in raw_line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue

        rank_text, item, lane, current_state, next_artifact, operator_note = cells
        if not rank_text.isdigit():
            continue

        artifact_value = _normalize_string(next_artifact)
        note_value = _normalize_string(operator_note)
        combined_notes = None
        if artifact_value and note_value:
            combined_notes = f"Exact next artifact: {artifact_value} | {note_value}"
        elif artifact_value:
            combined_notes = f"Exact next artifact: {artifact_value}"
        else:
            combined_notes = note_value

        records.append(
            LanePriorityRecord(
                lane=lane,
                priority_rank=int(rank_text),
                item_id=_slugify(item),
                title=item,
                status=current_state,
                source_surface=source_surface,
                notes=combined_notes,
            )
        )

    return records


def upsert_task_packets(db: Session, packets: list[TaskPacketRecord]) -> int:
    count = 0
    for packet in packets:
        db.execute(
            text(
                """
                INSERT INTO public.mcp_task_packets (
                    task_id,
                    title,
                    lane,
                    primary_repo,
                    status,
                    action_type,
                    risk_level,
                    preferred_model_tier,
                    review_gate,
                    briefing_path,
                    packet_json,
                    claimed_by,
                    created_at,
                    updated_at
                )
                VALUES (
                    :task_id,
                    :title,
                    :lane,
                    :primary_repo,
                    :status,
                    :action_type,
                    :risk_level,
                    :preferred_model_tier,
                    :review_gate,
                    :briefing_path,
                    CAST(:packet_json AS jsonb),
                    :claimed_by,
                    COALESCE(CAST(:created_at AS timestamptz), NOW()),
                    COALESCE(CAST(:updated_at AS timestamptz), NOW())
                )
                ON CONFLICT (task_id) DO UPDATE
                SET title = EXCLUDED.title,
                    lane = EXCLUDED.lane,
                    primary_repo = EXCLUDED.primary_repo,
                    status = EXCLUDED.status,
                    action_type = EXCLUDED.action_type,
                    risk_level = EXCLUDED.risk_level,
                    preferred_model_tier = EXCLUDED.preferred_model_tier,
                    review_gate = EXCLUDED.review_gate,
                    briefing_path = EXCLUDED.briefing_path,
                    packet_json = EXCLUDED.packet_json,
                    claimed_by = EXCLUDED.claimed_by,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "task_id": packet.task_id,
                "title": packet.title,
                "lane": packet.lane,
                "primary_repo": packet.primary_repo,
                "status": packet.status,
                "action_type": packet.action_type,
                "risk_level": packet.risk_level,
                "preferred_model_tier": packet.preferred_model_tier,
                "review_gate": packet.review_gate,
                "briefing_path": packet.briefing_path,
                "packet_json": json.dumps(packet.packet_json),
                "claimed_by": packet.claimed_by,
                "created_at": packet.created_at,
                "updated_at": packet.updated_at,
            },
        )
        count += 1
    return count


def replace_lane_priorities(db: Session, priorities: list[LanePriorityRecord], source_surface: str) -> int:
    db.execute(
        text(
            """
            DELETE FROM public.mcp_lane_priorities
            WHERE source_surface = :source_surface
            """
        ),
        {"source_surface": source_surface},
    )

    for record in priorities:
        db.execute(
            text(
                """
                INSERT INTO public.mcp_lane_priorities (
                    lane,
                    priority_rank,
                    item_id,
                    title,
                    status,
                    source_surface,
                    notes
                )
                VALUES (
                    :lane,
                    :priority_rank,
                    :item_id,
                    :title,
                    :status,
                    :source_surface,
                    :notes
                )
                ON CONFLICT (lane, priority_rank, item_id) DO UPDATE
                SET title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    source_surface = EXCLUDED.source_surface,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                """
            ),
            {
                "lane": record.lane,
                "priority_rank": record.priority_rank,
                "item_id": record.item_id,
                "title": record.title,
                "status": record.status,
                "source_surface": record.source_surface,
                "notes": record.notes,
            },
        )

    return len(priorities)