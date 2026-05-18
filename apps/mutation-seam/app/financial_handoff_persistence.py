from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.audit.logger import record_audit_event
from app.auth.jwt import Actor
from app.auth.role_guard import check_scope
from app.customer_completion_persistence import (
    COMPLETION_EVIDENCE_AUTHORITY,
    CUSTOMER_DELIVERY_AUTHORITY,
    CUSTOMER_REPORTING_AUTHORITY,
    LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
    load_customer_completion_status,
)
from app.db.memory_store import store
from app.durable_field_record_persistence import (
    LANE_279_FIELD_AUTH_RECORD_ID,
    LANE_280_STATUS_RECORD_ID,
    LANE_281_FIELD_RECORD_ID,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
)
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.idempotency.store import save_idempotency
from app.production_tracking_persistence import (
    LANE_282_PRODUCTION_TRACKING_RECORD_ID,
    PRODUCTION_TRACKING_AUTHORITY,
)


FINANCIAL_HANDOFF_ENTITY_TYPE = "financial_handoff_record"
FINANCIAL_HANDOFF_ACTION_TYPE = "create_financial_handoff_baseline"
FINANCIAL_HANDOFF_ROUTE = "/api/v1/mutations/financial-handoff"
FINANCIAL_HANDOFF_STATUS_ROUTE = "/api/v1/reads/financial-handoff-status"
FINANCIAL_HANDOFF_PERSISTENCE_VERSION = "pm_lane_284_financial_handoff_v1"
FINANCIAL_HANDOFF_AUTHORITY = "admitted_by_pm_lane_284_zero_finance_handoff_baseline"
LABOR_RECONCILIATION_AUTHORITY = "admitted_by_pm_lane_284_zero_labor_reconciliation_baseline"
NOT_ADMITTED = "not_admitted"

LANE_284_FINANCIAL_HANDOFF_RECORD_ID = "pm-lane-284-financial-handoff-temp-power-2026-05-18"
LANE_284_IDEMPOTENCY_KEY = "pm-lane-284-financial-handoff:pm-import-project-miner-temp-power:2026-05-18"
LANE_284_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "007_pm_lane_284_financial_handoff_records.sql"
)
_SCHEMA_READY = False

EXPECTED_COUNTS = {
    "workpackage_count": 7,
    "task_ready_count": 15,
    "apparatus_ready_count": 184,
    "assignment_count": 184,
    "unique_assignment_apparatus_count": 184,
    "issue_count": 0,
    "durable_field_record_count": 1,
    "production_tracking_record_count": 1,
    "customer_completion_record_count": 1,
    "production_quantity_count": 0,
    "labor_entry_count": 0,
    "actual_labor_hours": 0.0,
    "apparatus_progress_count": 0,
    "progress_update_count": 0,
    "customer_report_count": 0,
    "completion_evidence_count": 0,
    "customer_delivery_event_count": 0,
    "billing_export_count": 0,
    "payroll_export_count": 0,
    "invoice_record_count": 0,
    "payroll_record_count": 0,
    "accounting_record_count": 0,
    "labor_reconciliation_entry_count": 0,
    "external_finance_sync_count": 0,
    "customer_billing_delivery_count": 0,
    "billable_amount_total": 0.0,
    "payroll_amount_total": 0.0,
}

REQUIRED_PAYLOAD_FIELDS = {
    "financial_handoff_record_id",
    "idempotency_key",
    "project_id",
    "record_date",
    "record_kind",
    "record_status",
    "record_scope",
    "source_import_candidate_id",
    "source_import_fingerprint",
    "field_authorization_record_id",
    "schedule_status_record_id",
    "durable_field_record_id",
    "production_tracking_record_id",
    "customer_completion_record_id",
    "workpackage_count",
    "task_ready_count",
    "apparatus_ready_count",
    "assignment_count",
    "unique_assignment_apparatus_count",
    "issue_count",
    "durable_field_record_count",
    "production_tracking_record_count",
    "customer_completion_record_count",
    "production_quantity_count",
    "labor_entry_count",
    "actual_labor_hours",
    "apparatus_progress_count",
    "progress_update_count",
    "customer_report_count",
    "completion_evidence_count",
    "customer_delivery_event_count",
    "billing_export_artifacts",
    "billing_export_count",
    "payroll_export_artifacts",
    "payroll_export_count",
    "invoice_records",
    "invoice_record_count",
    "payroll_records",
    "payroll_record_count",
    "accounting_records",
    "accounting_record_count",
    "labor_reconciliation_entries",
    "labor_reconciliation_entry_count",
    "external_finance_sync_events",
    "external_finance_sync_count",
    "customer_billing_delivery_events",
    "customer_billing_delivery_count",
    "billable_amount_total",
    "payroll_amount_total",
    "production_tracking_authority",
    "customer_reporting_authority",
    "completion_evidence_authority",
    "customer_delivery_authority",
    "financial_handoff_authority",
    "labor_reconciliation_authority",
    "finance_authority",
    "billing_export_authority",
    "payroll_export_authority",
    "invoice_authority",
    "accounting_authority",
    "external_finance_sync_authority",
    "customer_billing_delivery_authority",
    "daily_summary",
}

OPTIONAL_PAYLOAD_FIELDS = {
    "financial_handoff_evidence",
    "pm_review_notes",
}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def _ensure_financial_handoff_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY or os.getenv("SEAM_STORE_BACKEND") == "memory":
        return
    if type(store).__name__ != "SupabaseStore":
        _SCHEMA_READY = True
        return

    from app.db.supabase_store import _conn_get

    with _conn_get().cursor() as cur:
        cur.execute("SELECT to_regclass('seam.financial_handoff_records') IS NOT NULL")
        exists = bool(cur.fetchone()[0])
        if not exists:
            cur.execute(LANE_284_MIGRATION_PATH.read_text(encoding="utf-8"))
    _SCHEMA_READY = True


def _records() -> Any:
    _ensure_financial_handoff_schema()
    return store.financial_handoff_records


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _customer_completion_readback() -> tuple[Dict[str, Any], list[Dict[str, Any]]]:
    customer_status = load_customer_completion_status()
    customer_records = [
        row for row in _values(store.customer_completion_records)
        if row.get("id") == LANE_283_CUSTOMER_COMPLETION_RECORD_ID
        and row.get("project_id") == TEMP_POWER_PROJECT_ID
        and row.get("record_status") == "recorded"
    ]
    return customer_status, customer_records


def _temp_power_preconditions() -> Dict[str, Any]:
    customer_status, customer_records = _customer_completion_readback()
    current_customer = customer_records[0] if customer_records else {}
    upstream_counts = dict((customer_status.get("preconditions") or {}).get("counts") or {})
    counts: Dict[str, Any] = {
        "workpackage_count": upstream_counts.get("workpackage_count"),
        "task_ready_count": upstream_counts.get("task_ready_count"),
        "apparatus_ready_count": upstream_counts.get("apparatus_ready_count"),
        "assignment_count": upstream_counts.get("assignment_count"),
        "unique_assignment_apparatus_count": upstream_counts.get("unique_assignment_apparatus_count"),
        "issue_count": upstream_counts.get("issue_count"),
        "durable_field_record_count": upstream_counts.get("durable_field_record_count"),
        "production_tracking_record_count": upstream_counts.get("production_tracking_record_count"),
        "customer_completion_record_count": len(customer_records),
        "production_quantity_count": current_customer.get("production_quantity_count"),
        "labor_entry_count": current_customer.get("labor_entry_count"),
        "actual_labor_hours": current_customer.get("actual_labor_hours"),
        "apparatus_progress_count": current_customer.get("apparatus_progress_count"),
        "progress_update_count": current_customer.get("progress_update_count"),
        "customer_report_count": current_customer.get("customer_report_count"),
        "completion_evidence_count": current_customer.get("completion_evidence_count"),
        "customer_delivery_event_count": len(current_customer.get("customer_delivery_events") or []),
        "billing_export_count": 0,
        "payroll_export_count": 0,
        "invoice_record_count": 0,
        "payroll_record_count": 0,
        "accounting_record_count": 0,
        "labor_reconciliation_entry_count": 0,
        "external_finance_sync_count": 0,
        "customer_billing_delivery_count": 0,
        "billable_amount_total": 0.0,
        "payroll_amount_total": 0.0,
    }

    mismatches = []
    for field, expected in EXPECTED_COUNTS.items():
        if counts.get(field) != expected:
            mismatches.append({"field": field, "expected": expected, "actual": counts.get(field)})

    if customer_status.get("classification") != "customer_completion_baseline_recorded":
        mismatches.append(
            {
                "field": "customer_completion_status",
                "expected": "customer_completion_baseline_recorded",
                "actual": customer_status.get("classification"),
            }
        )

    if current_customer:
        expected_customer_values = {
            "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
            "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
            "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
            "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
            "finance_authority": NOT_ADMITTED,
            "billing_authority": NOT_ADMITTED,
            "payroll_authority": NOT_ADMITTED,
            "invoice_authority": NOT_ADMITTED,
            "accounting_authority": NOT_ADMITTED,
        }
        for field, expected in expected_customer_values.items():
            if current_customer.get(field) != expected:
                mismatches.append({"field": f"customer.{field}", "expected": expected, "actual": current_customer.get(field)})

    return {
        "valid": not mismatches,
        "counts": counts,
        "mismatches": mismatches,
        "customer_completion_status": customer_status,
        "customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
    }


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
        entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _normalize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = {field: payload.get(field) for field in sorted(REQUIRED_PAYLOAD_FIELDS)}
    for field in sorted(OPTIONAL_PAYLOAD_FIELDS):
        if field in payload:
            normalized[field] = payload.get(field)
    for field in [
        "billing_export_artifacts",
        "payroll_export_artifacts",
        "invoice_records",
        "payroll_records",
        "accounting_records",
        "labor_reconciliation_entries",
        "external_finance_sync_events",
        "customer_billing_delivery_events",
    ]:
        if normalized.get(field) is None:
            normalized[field] = []
    if normalized.get("financial_handoff_evidence") is None:
        normalized["financial_handoff_evidence"] = {}
    normalized["daily_summary"] = str(normalized.get("daily_summary") or "").strip()
    if "pm_review_notes" in normalized:
        normalized["pm_review_notes"] = str(normalized.get("pm_review_notes") or "").strip()
    return normalized


def _expected_values() -> Dict[str, Any]:
    return {
        "financial_handoff_record_id": LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
        "idempotency_key": LANE_284_IDEMPOTENCY_KEY,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "record_kind": "financial_handoff_zero_output_baseline",
        "record_status": "recorded",
        "record_scope": "financial_handoff_baseline_no_billing_payroll_invoice_accounting_or_sync",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
        "financial_handoff_authority": FINANCIAL_HANDOFF_AUTHORITY,
        "labor_reconciliation_authority": LABOR_RECONCILIATION_AUTHORITY,
        "finance_authority": NOT_ADMITTED,
        "billing_export_authority": NOT_ADMITTED,
        "payroll_export_authority": NOT_ADMITTED,
        "invoice_authority": NOT_ADMITTED,
        "accounting_authority": NOT_ADMITTED,
        "external_finance_sync_authority": NOT_ADMITTED,
        "customer_billing_delivery_authority": NOT_ADMITTED,
        **EXPECTED_COUNTS,
    }


def _validate_payload(
    request: MutationRequest,
    preconditions: Mapping[str, Any],
) -> Optional[MutationResponse]:
    payload = request.payload or {}
    unknown_fields = sorted(set(payload) - REQUIRED_PAYLOAD_FIELDS - OPTIONAL_PAYLOAD_FIELDS)
    if unknown_fields:
        return _invalid_payload_response(
            request,
            "Financial handoff payload contains fields outside the admitted PM Lane 284 contract.",
            detail={"unknown_fields": unknown_fields},
        )

    missing_fields = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if payload.get(field) in (None, ""))
    if missing_fields:
        return _invalid_payload_response(
            request,
            "Financial handoff payload is missing required fields.",
            detail={"missing_fields": missing_fields},
        )

    mismatches = []
    for field, expected in _expected_values().items():
        actual = payload.get(field)
        if actual != expected:
            mismatches.append({"field": field, "expected": expected, "actual": actual})

    if request.idempotency_key != LANE_284_IDEMPOTENCY_KEY:
        mismatches.append(
            {
                "field": "envelope.idempotency_key",
                "expected": LANE_284_IDEMPOTENCY_KEY,
                "actual": request.idempotency_key,
            }
        )
    if request.entity_id and request.entity_id != LANE_284_FINANCIAL_HANDOFF_RECORD_ID:
        mismatches.append(
            {
                "field": "envelope.entity_id",
                "expected": LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
                "actual": request.entity_id,
            }
        )

    for field in [
        "billing_export_artifacts",
        "payroll_export_artifacts",
        "invoice_records",
        "payroll_records",
        "accounting_records",
        "labor_reconciliation_entries",
        "external_finance_sync_events",
        "customer_billing_delivery_events",
    ]:
        if payload.get(field) != []:
            mismatches.append({"field": field, "expected": [], "actual": payload.get(field)})

    if not str(payload.get("daily_summary") or "").strip():
        mismatches.append({"field": "daily_summary", "expected": "non-empty", "actual": payload.get("daily_summary")})

    precondition_counts = dict(preconditions.get("counts") or {})
    for field in EXPECTED_COUNTS:
        if payload.get(field) != precondition_counts.get(field):
            mismatches.append(
                {
                    "field": f"payload.{field}_vs_readback",
                    "expected": precondition_counts.get(field),
                    "actual": payload.get(field),
                }
            )

    if mismatches:
        return _invalid_payload_response(
            request,
            "Financial handoff payload does not match the admitted PM Lane 284 contract.",
            detail={"mismatches": mismatches},
        )
    return None


def _record_matches(record: Mapping[str, Any], normalized_payload: Mapping[str, Any]) -> bool:
    return _stable_json(record.get("financial_handoff_payload") or {}) == _stable_json(normalized_payload)


def _response(
    *,
    status: str,
    mutation_id: str,
    action_type: str,
    record: Mapping[str, Any],
    audit_event_id: Optional[str],
) -> MutationResponse:
    return MutationResponse(
        status=status,
        mutation_id=mutation_id,
        entity_id=str(record["id"]),
        entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
        action_type=action_type,
        new_state=dict(record),
        audit_event_id=audit_event_id,
    )


def persist_financial_handoff_record(request: MutationRequest, actor: Actor) -> MutationResponse:
    if request.action_type != FINANCIAL_HANDOFF_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown financial handoff action type: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Financial handoff baseline persistence cannot be queued offline.",
            entity_id=request.entity_id or LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
            entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Financial handoff baseline persistence requires mutation_class C.",
            entity_id=request.entity_id or LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
            entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist this PM Lane 284 financial handoff baseline.",
            entity_id=request.entity_id or LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
            entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the Temp Power project.",
            entity_id=request.entity_id or LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
            entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    preconditions = _temp_power_preconditions()
    if not preconditions["valid"]:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Financial handoff baseline requires the PM Lane 283 customer completion baseline record.",
            entity_id=request.entity_id or LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
            entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
            action_type=request.action_type,
            detail=preconditions,
        )

    payload_error = _validate_payload(request, preconditions)
    if payload_error:
        return payload_error

    normalized_payload = _normalize_payload(request.payload)
    records = _records()
    existing = records.get(LANE_284_FINANCIAL_HANDOFF_RECORD_ID)
    if existing:
        if not _record_matches(existing, normalized_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Existing financial handoff baseline does not match the submitted replay payload.",
                entity_id=LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
                entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"financial_handoff_record_id": LANE_284_FINANCIAL_HANDOFF_RECORD_ID},
            )
        return _response(
            status="idempotent_hit",
            mutation_id=str(existing.get("mutation_id") or f"mut-{uuid4()}"),
            action_type=request.action_type,
            record=existing,
            audit_event_id=str(existing.get("audit_event_id") or "") or None,
        )

    recorded_at = _server_timestamp()
    mutation_id = f"mut-{uuid4()}"
    audit_event_id = f"audit-{uuid4()}"
    record = {
        "id": LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": normalized_payload["record_date"],
        "record_kind": normalized_payload["record_kind"],
        "record_status": normalized_payload["record_status"],
        "created_by_actor_id": actor.actor_id,
        "created_by_role": actor.actor_role,
        "recorded_at_utc": recorded_at,
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
        "financial_handoff_authority": FINANCIAL_HANDOFF_AUTHORITY,
        "labor_reconciliation_authority": LABOR_RECONCILIATION_AUTHORITY,
        "finance_authority": NOT_ADMITTED,
        "billing_export_authority": NOT_ADMITTED,
        "payroll_export_authority": NOT_ADMITTED,
        "invoice_authority": NOT_ADMITTED,
        "accounting_authority": NOT_ADMITTED,
        "external_finance_sync_authority": NOT_ADMITTED,
        "customer_billing_delivery_authority": NOT_ADMITTED,
        "idempotency_key": LANE_284_IDEMPOTENCY_KEY,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "persistence_version": FINANCIAL_HANDOFF_PERSISTENCE_VERSION,
        "route": FINANCIAL_HANDOFF_ROUTE,
        "status_route": FINANCIAL_HANDOFF_STATUS_ROUTE,
        "financial_handoff_payload": normalized_payload,
        "precondition_readback": _json_safe(preconditions),
        "billing_export_artifacts": [],
        "billing_export_count": 0,
        "payroll_export_artifacts": [],
        "payroll_export_count": 0,
        "invoice_records": [],
        "invoice_record_count": 0,
        "payroll_records": [],
        "payroll_record_count": 0,
        "accounting_records": [],
        "accounting_record_count": 0,
        "labor_reconciliation_entries": [],
        "labor_reconciliation_entry_count": 0,
        "external_finance_sync_events": [],
        "external_finance_sync_count": 0,
        "customer_billing_delivery_events": [],
        "customer_billing_delivery_count": 0,
        "billable_amount_total": 0.0,
        "payroll_amount_total": 0.0,
        "production_quantity_count": 0,
        "labor_entry_count": 0,
        "actual_labor_hours": 0.0,
        "apparatus_progress_count": 0,
        "progress_update_count": 0,
        "customer_report_count": 0,
        "completion_evidence_count": 0,
        "daily_summary": normalized_payload["daily_summary"],
        "financial_handoff_evidence": normalized_payload.get("financial_handoff_evidence") or {},
    }
    if normalized_payload.get("pm_review_notes"):
        record["pm_review_notes"] = normalized_payload["pm_review_notes"]

    records[LANE_284_FINANCIAL_HANDOFF_RECORD_ID] = record
    audit_request = request.model_copy(update={"entity_id": LANE_284_FINANCIAL_HANDOFF_RECORD_ID, "payload": record})
    record_audit_event(
        actor=actor,
        request=audit_request,
        from_state={},
        to_state=record,
        mutation_id=mutation_id,
        event_id=audit_event_id,
        entity_type=FINANCIAL_HANDOFF_ENTITY_TYPE,
    )
    response = _response(
        status="accepted",
        mutation_id=mutation_id,
        action_type=request.action_type,
        record=record,
        audit_event_id=audit_event_id,
    )
    save_idempotency(request.idempotency_key, response)
    return response


def load_financial_handoff_status() -> Dict[str, Any]:
    try:
        rows = [
            row for row in _values(_records())
            if row.get("project_id") == TEMP_POWER_PROJECT_ID
        ]
    except Exception as exc:  # pragma: no cover - exercised through broken-store tests if needed.
        return {
            "classification": "financial_handoff_storage_unavailable",
            "storage_available": False,
            "route": FINANCIAL_HANDOFF_STATUS_ROUTE,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "financial_handoff_authority": FINANCIAL_HANDOFF_AUTHORITY,
            "labor_reconciliation_authority": LABOR_RECONCILIATION_AUTHORITY,
            "finance_authority": NOT_ADMITTED,
            "billing_export_authority": NOT_ADMITTED,
            "payroll_export_authority": NOT_ADMITTED,
            "invoice_authority": NOT_ADMITTED,
            "accounting_authority": NOT_ADMITTED,
            "external_finance_sync_authority": NOT_ADMITTED,
            "customer_billing_delivery_authority": NOT_ADMITTED,
        }

    preconditions = _temp_power_preconditions()
    latest = sorted(rows, key=lambda row: str(row.get("recorded_at_utc") or row.get("created_at") or ""), reverse=True)
    current = next((row for row in latest if row.get("id") == LANE_284_FINANCIAL_HANDOFF_RECORD_ID), None)
    if not current:
        return {
            "classification": "no_financial_handoff_record",
            "storage_available": True,
            "route": FINANCIAL_HANDOFF_STATUS_ROUTE,
            "expected_financial_handoff_record_id": LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
            "record_count": len(rows),
            "preconditions": preconditions,
            "financial_handoff_authority": FINANCIAL_HANDOFF_AUTHORITY,
            "labor_reconciliation_authority": LABOR_RECONCILIATION_AUTHORITY,
            "finance_authority": NOT_ADMITTED,
            "billing_export_authority": NOT_ADMITTED,
            "payroll_export_authority": NOT_ADMITTED,
            "invoice_authority": NOT_ADMITTED,
            "accounting_authority": NOT_ADMITTED,
            "external_finance_sync_authority": NOT_ADMITTED,
            "customer_billing_delivery_authority": NOT_ADMITTED,
        }

    return {
        "classification": "financial_handoff_baseline_recorded",
        "storage_available": True,
        "route": FINANCIAL_HANDOFF_STATUS_ROUTE,
        "financial_handoff_record_id": current.get("id"),
        "record_count": len(rows),
        "record_date": current.get("record_date"),
        "record_kind": current.get("record_kind"),
        "record_status": current.get("record_status"),
        "mutation_id": current.get("mutation_id"),
        "audit_event_id": current.get("audit_event_id"),
        "source_import_candidate_id": current.get("source_import_candidate_id"),
        "source_import_fingerprint": current.get("source_import_fingerprint"),
        "field_authorization_record_id": current.get("field_authorization_record_id"),
        "schedule_status_record_id": current.get("schedule_status_record_id"),
        "durable_field_record_id": current.get("durable_field_record_id"),
        "production_tracking_record_id": current.get("production_tracking_record_id"),
        "customer_completion_record_id": current.get("customer_completion_record_id"),
        "preconditions": preconditions,
        "production_tracking_authority": current.get("production_tracking_authority") or PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": current.get("customer_reporting_authority") or CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": current.get("completion_evidence_authority") or COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": current.get("customer_delivery_authority") or CUSTOMER_DELIVERY_AUTHORITY,
        "financial_handoff_authority": current.get("financial_handoff_authority") or FINANCIAL_HANDOFF_AUTHORITY,
        "labor_reconciliation_authority": current.get("labor_reconciliation_authority") or LABOR_RECONCILIATION_AUTHORITY,
        "finance_authority": current.get("finance_authority") or NOT_ADMITTED,
        "billing_export_authority": current.get("billing_export_authority") or NOT_ADMITTED,
        "payroll_export_authority": current.get("payroll_export_authority") or NOT_ADMITTED,
        "invoice_authority": current.get("invoice_authority") or NOT_ADMITTED,
        "accounting_authority": current.get("accounting_authority") or NOT_ADMITTED,
        "external_finance_sync_authority": current.get("external_finance_sync_authority") or NOT_ADMITTED,
        "customer_billing_delivery_authority": current.get("customer_billing_delivery_authority") or NOT_ADMITTED,
        "billing_export_count": current.get("billing_export_count"),
        "payroll_export_count": current.get("payroll_export_count"),
        "invoice_record_count": current.get("invoice_record_count"),
        "payroll_record_count": current.get("payroll_record_count"),
        "accounting_record_count": current.get("accounting_record_count"),
        "labor_reconciliation_entry_count": current.get("labor_reconciliation_entry_count"),
        "external_finance_sync_count": current.get("external_finance_sync_count"),
        "customer_billing_delivery_count": current.get("customer_billing_delivery_count"),
        "billable_amount_total": current.get("billable_amount_total"),
        "payroll_amount_total": current.get("payroll_amount_total"),
        "production_quantity_count": current.get("production_quantity_count"),
        "labor_entry_count": current.get("labor_entry_count"),
        "actual_labor_hours": current.get("actual_labor_hours"),
        "customer_report_count": current.get("customer_report_count"),
        "completion_evidence_count": current.get("completion_evidence_count"),
    }
