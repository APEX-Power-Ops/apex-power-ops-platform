from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import tempfile
from typing import Optional, Tuple

import psycopg
import psycopg.errors

from .classify import classify
from .extract import extract_workbook
from .model import PARSER_VERSION, PAYLOAD_SCHEMA_VERSION
from .validate import validate_payload


class ActiveRunExists(Exception):
    pass


def _classify_conflict(cur, project_number):
    cur.execute(
        "select id from ops.projects where project_number = %s limit 1",
        (project_number,),
    )
    row = cur.fetchone()
    if row is None:
        return None, "none"
    project_id = str(row[0])

    cur.execute(
        "select 1 from ops.billing_application where project_id = %s limit 1",
        (project_id,),
    )
    if cur.fetchone() is not None:
        return project_id, "billed"

    cur.execute(
        "select 1 from ops.revenue_recognition_event where project_id = %s limit 1",
        (project_id,),
    )
    if cur.fetchone() is not None:
        return project_id, "recognized"

    cur.execute(
        "select 1 from ops.scope_quote sq"
        " join ops.scopes s on s.id = sq.scope_id"
        " where s.project_id = %s and sq.is_frozen = true"
        " limit 1",
        (project_id,),
    )
    if cur.fetchone() is not None:
        return project_id, "frozen"

    return project_id, "none"


def create_run(
    dsn,
    *,
    uploaded_by,
    filename,
    raw_bytes,
    content_type,
):
    with tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False) as tf:
        tf.write(raw_bytes)
        tmp_path = pathlib.Path(tf.name)

    try:
        payload = extract_workbook(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    project_number = payload.project.project_number
    source_format = classify(payload)
    findings = validate_payload(payload, source_format=source_format, n4_defaulted=False)

    if source_format in ("flat_quote", "unsupported"):
        pre_status = "rejected"
    else:
        pre_status = None

    payload_json = json.dumps(dataclasses.asdict(payload), default=str)
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    byte_size = len(raw_bytes)

    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select pg_advisory_xact_lock(hashtext(%s))",
                    (project_number,),
                )

                project_id, conflict_kind = _classify_conflict(cur, project_number)

                if pre_status is not None:
                    status = pre_status
                elif conflict_kind != "none":
                    status = "revision_blocked"
                else:
                    status = "parsed"

                if status in ("parsed", "reviewing"):
                    cur.execute(
                        "update ops.intake_runs"
                        " set status = %s::ops.intake_run_status, updated_at = now()"
                        " where project_number = %s"
                        " and status in (%s::ops.intake_run_status, %s::ops.intake_run_status)",
                        ("superseded", project_number, "parsed", "reviewing"),
                    )

                cur.execute(
                    "insert into ops.intake_runs ("
                    "   project_number, project_id, source_format, status, conflict_kind,"
                    "   payload_schema_version, parser_version,"
                    "   canonical_payload_json, review_payload_json,"
                    "   review_payload_version, uploaded_by"
                    ") values ("
                    "   %s, %s, %s::ops.intake_source_format, %s::ops.intake_run_status,"
                    "   %s::ops.intake_conflict_kind,"
                    "   %s, %s, %s::jsonb, %s::jsonb, 1, %s"
                    ") returning id",
                    (
                        project_number,
                        project_id,
                        source_format,
                        status,
                        conflict_kind,
                        PAYLOAD_SCHEMA_VERSION,
                        PARSER_VERSION,
                        payload_json,
                        payload_json,
                        str(uploaded_by),
                    ),
                )
                run_id = str(cur.fetchone()[0])

                cur.execute(
                    "insert into ops.intake_source_files ("
                    "   run_id, filename, content_type, byte_size, sha256, raw_bytes"
                    ") values (%s, %s, %s, %s, %s, %s)",
                    (run_id, filename, content_type, byte_size, sha256, raw_bytes),
                )

                for finding in findings:
                    cur.execute(
                        "insert into ops.intake_validation_findings ("
                        "   run_id, payload_version, severity, code, ok, message, diagnostic_detail"
                        ") values (%s, 1, %s, %s, %s, %s, %s)",
                        (
                            run_id,
                            finding.severity,
                            finding.code,
                            finding.ok,
                            finding.message,
                            finding.diagnostic_detail,
                        ),
                    )

            conn.commit()

    except psycopg.errors.UniqueViolation as exc:
        if "uq_intake_one_active" in str(exc):
            raise ActiveRunExists(
                "An active intake run already exists for project " + repr(project_number)
            ) from exc
        raise

    return {
        "run_id": run_id,
        "status": status,
        "conflict_kind": conflict_kind,
        "source_format": source_format,
        "findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "ok": f.ok,
                "message": f.message,
            }
            for f in findings
        ],
        "review_payload": dataclasses.asdict(payload),
    }


def get_run(dsn, run_id):
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select id, project_number, project_id, source_format, status,"
                "       conflict_kind, payload_schema_version, parser_version,"
                "       review_payload_json, review_payload_version,"
                "       uploaded_by, uploaded_at, approved_by, approved_at, rejected_reason"
                "  from ops.intake_runs"
                " where id = %s",
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError("run not found: " + repr(run_id))

            (
                r_id, project_number, project_id, source_format, status,
                conflict_kind, payload_schema_version, parser_version,
                review_payload_json, review_payload_version,
                uploaded_by, uploaded_at, approved_by, approved_at, rejected_reason,
            ) = row

            cur.execute(
                "select code, severity, ok, message"
                "  from ops.intake_validation_findings"
                " where run_id = %s"
                " order by created_at",
                (run_id,),
            )
            findings = [
                {"code": c, "severity": s, "ok": o, "message": m}
                for c, s, o, m in cur.fetchall()
            ]

    return {
        "run_id": str(r_id),
        "project_number": project_number,
        "project_id": str(project_id) if project_id else None,
        "source_format": source_format,
        "status": status,
        "conflict_kind": conflict_kind,
        "payload_schema_version": payload_schema_version,
        "parser_version": parser_version,
        "review_payload": review_payload_json,
        "review_payload_version": review_payload_version,
        "uploaded_by": str(uploaded_by),
        "uploaded_at": uploaded_at.isoformat() if uploaded_at else None,
        "approved_by": str(approved_by) if approved_by else None,
        "approved_at": approved_at.isoformat() if approved_at else None,
        "rejected_reason": rejected_reason,
        "findings": findings,
    }