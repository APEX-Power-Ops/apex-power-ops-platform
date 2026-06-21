from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import tempfile
from collections import Counter
from typing import Optional, Tuple

import psycopg
import psycopg.errors

from .classify import classify
from .extract import extract_workbook
from .model import (
    PARSER_VERSION, PAYLOAD_SCHEMA_VERSION,
    IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn, StandardHourIn,
)
from .validate import validate_payload


class ActiveRunExists(Exception):
    pass


def _payload_from_dict(d):
    """Reconstruct an IntakePayload from a plain dict (e.g. review_payload_json)."""
    proj = ProjectIn(**{
        k: v for k, v in d["project"].items()
        if k in {f.name for f in dataclasses.fields(ProjectIn)}
    })
    scopes = []
    for sd in d.get("scopes", []):
        qd = sd.get("quote", {})
        quote = ScopeQuoteIn(**{
            k: v for k, v in qd.items()
            if k in {f.name for f in dataclasses.fields(ScopeQuoteIn)}
        })
        lines = []
        for ld in sd.get("lines", []):
            line = QuoteLineIn(**{
                k: v for k, v in ld.items()
                if k in {f.name for f in dataclasses.fields(QuoteLineIn)}
            })
            lines.append(line)
        scope = ScopeIn(
            scope_name=sd["scope_name"],
            scope_type=sd.get("scope_type", "OTHER"),
            sort_order=sd.get("sort_order", 0),
            quote=quote,
            lines=lines,
        )
        scopes.append(scope)
    standard_hours = []
    for shd in d.get("standard_hours", []):
        sh = StandardHourIn(**{
            k: v for k, v in shd.items()
            if k in {f.name for f in dataclasses.fields(StandardHourIn)}
        })
        standard_hours.append(sh)
    return IntakePayload(project=proj, scopes=scopes, standard_hours=standard_hours)


def _assert_no_cross_scope_move(canonical, review):
    """Build line_uid -> scope_name maps; raise if any uid moved across scopes."""
    canon_map = {}
    for scope in canonical.get("scopes", []):
        scope_name = scope["scope_name"]
        for line in scope.get("lines", []):
            uid = line.get("line_uid")
            if uid is not None:
                canon_map[uid] = scope_name

    review_map = {}
    for scope in review.get("scopes", []):
        scope_name = scope["scope_name"]
        for line in scope.get("lines", []):
            uid = line.get("line_uid")
            if uid is not None:
                review_map[uid] = scope_name

    for uid, canon_scope in canon_map.items():
        if uid in review_map and review_map[uid] != canon_scope:
            raise ValueError(
                "cross-scope line move forbidden: line_uid=" + repr(uid) +
                " moved from scope " + repr(canon_scope) +
                " to " + repr(review_map[uid])
            )


_LINE_MUTABLE = frozenset({"section", "hrs_per_unit"})


def _assert_review_within_allowlist(canonical, review):
    """Default-deny integrity gate. Lines joined by line_uid not position."""
    # 1. Project: pin every field
    canon_proj = canonical.get("project", {})
    rev_proj = review.get("project", {})
    all_proj_keys = set(canon_proj) | set(rev_proj)
    for k in all_proj_keys:
        if canon_proj.get(k) != rev_proj.get(k):
            raise ValueError(
                "project field " + repr(k) + " is not mutable: " +
                "canonical=" + repr(canon_proj.get(k)) +
                ", review=" + repr(rev_proj.get(k))
            )

    # 2. Scope set
    canon_scopes = {s["scope_name"]: s for s in canonical.get("scopes", [])}
    rev_scopes = {s["scope_name"]: s for s in review.get("scopes", [])}
    if set(canon_scopes) != set(rev_scopes):
        raise ValueError(
            "scope set changed: " +
            "canonical=" + str(sorted(canon_scopes)) +
            ", review=" + str(sorted(rev_scopes))
        )

    for scope_name in canon_scopes:
        cs = canon_scopes[scope_name]
        rs = rev_scopes[scope_name]

        # 3. Scope quote: pin ALL fields
        cq = cs.get("quote", {})
        rq = rs.get("quote", {})
        all_quote_keys = set(cq) | set(rq)
        for k in all_quote_keys:
            if cq.get(k) != rq.get(k):
                raise ValueError(
                    "scope " + repr(scope_name) +
                    " quote field " + repr(k) + " is not mutable: " +
                    "canonical=" + repr(cq.get(k)) +
                    ", review=" + repr(rq.get(k))
                )

        # 4. Lines: exact same multiset of line_uid values
        canon_lines_list = cs.get("lines", [])
        rev_lines_list = rs.get("lines", [])

        canon_uid_counts = Counter(l.get("line_uid") for l in canon_lines_list)
        rev_uid_counts = Counter(l.get("line_uid") for l in rev_lines_list)

        for uid, cnt in rev_uid_counts.items():
            if cnt > 1:
                raise ValueError(
                    "scope " + repr(scope_name) +
                    ": line_uid " + repr(uid) +
                    " appears " + str(cnt) +
                    " times in review (duplicate line detected)"
                )

        if canon_uid_counts != rev_uid_counts:
            added = set(rev_uid_counts) - set(canon_uid_counts)
            removed = set(canon_uid_counts) - set(rev_uid_counts)
            raise ValueError(
                "scope " + repr(scope_name) + ": line_uid multiset changed " +
                "(added=" + str(sorted(str(u) for u in added)) +
                ", removed=" + str(sorted(str(u) for u in removed)) + ")"
            )

        # 5. Per-line: join by line_uid NOT position
        canon_by_uid = {l.get("line_uid"): l for l in canon_lines_list}
        rev_by_uid = {l.get("line_uid"): l for l in rev_lines_list}

        for uid, canon_line in canon_by_uid.items():
            rev_line = rev_by_uid[uid]
            all_line_keys = set(canon_line) | set(rev_line)
            for k in all_line_keys:
                if k in _LINE_MUTABLE:
                    continue
                if canon_line.get(k) != rev_line.get(k):
                    raise ValueError(
                        "scope " + repr(scope_name) +
                        " line " + repr(uid) +
                        ": field " + repr(k) + " is not mutable: " +
                        "canonical=" + repr(canon_line.get(k)) +
                        ", review=" + repr(rev_line.get(k))
                    )


def patch_review(dsn, run_id, *, review_payload):
    """Edit review payload; status guard; both integrity guards; persist; return updated run."""
    _ACTIVE_STATUSES = {"parsed", "reviewing"}

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select status, canonical_payload_json, review_payload_version, source_format"
                "  from ops.intake_runs"
                " where id = %s",
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError("run not found: " + repr(run_id))

            status, canonical_json, current_version, source_format = row

            if status not in _ACTIVE_STATUSES:
                raise ValueError(
                    "patch_review only allowed on parsed/reviewing runs; " +
                    "run " + repr(run_id) + " has status " + repr(status)
                )

            canonical = canonical_json if isinstance(canonical_json, dict) else json.loads(canonical_json)

            _assert_review_within_allowlist(canonical, review_payload)
            _assert_no_cross_scope_move(canonical, review_payload)

            new_version = current_version + 1

            cur.execute(
                "update ops.intake_runs"
                " set review_payload_json = %s::jsonb,"
                "     review_payload_version = %s,"
                "     status = %s::ops.intake_run_status,"
                "     updated_at = now()"
                " where id = %s",
                (
                    json.dumps(review_payload, default=str),
                    new_version,
                    "reviewing",
                    run_id,
                ),
            )

            updated_payload_obj = _payload_from_dict(review_payload)
            findings = validate_payload(
                updated_payload_obj,
                source_format=source_format,
                n4_defaulted=False,
            )

            for finding in findings:
                cur.execute(
                    "insert into ops.intake_validation_findings ("
                    "   run_id, payload_version, severity, code, ok, message, diagnostic_detail"
                    ") values (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        run_id,
                        new_version,
                        finding.severity,
                        finding.code,
                        finding.ok,
                        finding.message,
                        finding.diagnostic_detail,
                    ),
                )

        conn.commit()

    return get_run(dsn, run_id)


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