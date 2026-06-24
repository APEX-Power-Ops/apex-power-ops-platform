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
from .extract import extract_workbook, parse_json_payload
from .model import (
    PARSER_VERSION, PAYLOAD_SCHEMA_VERSION,
    IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn, StandardHourIn,
)
from .native import validate_envelope, recompute_content_hash, pivot_to_intake_payload, NATIVE_SCHEMA_VERSION, NATIVE_PARSER_VERSION
from .validate import validate_payload


class ActiveRunExists(Exception):
    pass


class RunNotActive(Exception):
    """patch_review was called on a run that is no longer parsed/reviewing (the API maps this to 409,
    distinct from a guard ValueError which is a 400). Raised under the run-row FOR UPDATE lock, so it
    reflects the committed lifecycle state, not a stale read."""
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


def _ve(msg):
    """Finance-redaction-safe ValueError for the review guards: strip any '$' from the
    message. A workbook-chosen scope name (and the line_uid it prefixes) is user-controlled and
    can carry a dollar sign; guard error messages must be value-free, like findings and the API
    error channel."""
    return ValueError(msg.replace("$", ""))


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
            raise _ve(
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
            raise _ve("project field " + repr(k) + " is not editable")

    # 2. Scope set
    canon_scopes = {s["scope_name"]: s for s in canonical.get("scopes", [])}
    rev_scopes = {s["scope_name"]: s for s in review.get("scopes", [])}
    if set(canon_scopes) != set(rev_scopes):
        raise _ve(
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
                # NB: message is value-FREE -- the quote dollar figures must never appear in an error
                # that can reach the PM surface (finance redaction applies to guard errors too).
                raise _ve(
                    "scope " + repr(scope_name) +
                    " quote field " + repr(k) + " is not editable"
                )

        # 4. Lines: exact same multiset of line_uid values
        canon_lines_list = cs.get("lines", [])
        rev_lines_list = rs.get("lines", [])

        canon_uid_counts = Counter(l.get("line_uid") for l in canon_lines_list)
        rev_uid_counts = Counter(l.get("line_uid") for l in rev_lines_list)

        for uid, cnt in rev_uid_counts.items():
            if cnt > 1:
                raise _ve(
                    "scope " + repr(scope_name) +
                    ": line_uid " + repr(uid) +
                    " appears " + str(cnt) +
                    " times in review (duplicate line detected)"
                )

        if canon_uid_counts != rev_uid_counts:
            added = set(rev_uid_counts) - set(canon_uid_counts)
            removed = set(canon_uid_counts) - set(rev_uid_counts)
            raise _ve(
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
                    raise _ve(
                        "scope " + repr(scope_name) +
                        " line " + repr(uid) +
                        ": field " + repr(k) + " is not editable"
                    )


def patch_review(dsn, run_id, *, review_payload):
    """Edit review payload; status guard; both integrity guards; persist; return updated run."""
    _ACTIVE_STATUSES = {"parsed", "reviewing"}

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # FOR UPDATE serializes concurrent patches (no lost-update / mixed-version findings) and
            # coordinates with approve_run's run-row lock: a save racing an approval either sees the
            # approved status here (-> ValueError, mapped to 409) or commits before approve takes the
            # row. patch_review takes only the run-row lock (never the project advisory lock), so it
            # cannot deadlock against approve (which takes advisory first, then the run row).
            cur.execute(
                "select status, canonical_payload_json, review_payload_version, source_format"
                "  from ops.intake_runs"
                " where id = %s for update",
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError("run not found: " + repr(run_id))

            status, canonical_json, current_version, source_format = row

            if status not in _ACTIVE_STATUSES:
                raise RunNotActive(
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
                " where id = %s"
                "   and status in ('parsed'::ops.intake_run_status, 'reviewing'::ops.intake_run_status)",
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


def _create_rejected_parse_envelope(dsn, *, uploaded_by, filename, content_type, raw_bytes,
                                    sha256, byte_size, parse_error):
    """Persist a GOVERNED rejected envelope for an UNPARSEABLE upload: a rejected intake_run + a
    blocking finding + the stored source bytes (for audit). No advisory lock and no domain writes --
    there is no real project. status='rejected' is outside uq_intake_one_active, so repeated bad
    uploads don't collide. Returns the same dict shape as a successful create_run."""
    project_number = ("UNPARSED:" + (filename or "upload"))[:200]
    detail = json.dumps({"parse_error": parse_error, "filename": filename}, default=str)
    message = "The uploaded file could not be parsed for intake"
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into ops.intake_runs ("
                "   project_number, source_format, status, conflict_kind,"
                "   payload_schema_version, parser_version,"
                "   canonical_payload_json, review_payload_json, review_payload_version, uploaded_by"
                ") values ("
                "   %s, %s::ops.intake_source_format, %s::ops.intake_run_status,"
                "   %s::ops.intake_conflict_kind, %s, %s, %s::jsonb, %s::jsonb, 1, %s"
                ") returning id",
                (project_number, "unsupported", "rejected", "none",
                 PAYLOAD_SCHEMA_VERSION, PARSER_VERSION, detail, detail, str(uploaded_by)),
            )
            run_id = str(cur.fetchone()[0])
            cur.execute(
                "insert into ops.intake_source_files ("
                "   run_id, filename, content_type, byte_size, sha256, raw_bytes"
                ") values (%s, %s, %s, %s, %s, %s)",
                (run_id, filename, content_type, byte_size, sha256, raw_bytes),
            )
            cur.execute(
                "insert into ops.intake_validation_findings ("
                "   run_id, payload_version, severity, code, ok, message, diagnostic_detail"
                ") values (%s, 1, 'blocking', 'parse_error', false, %s, %s)",
                (run_id, message, parse_error),
            )
        conn.commit()
    return {
        "run_id": run_id,
        "status": "rejected",
        "conflict_kind": "none",
        "source_format": "unsupported",
        "findings": [{"code": "parse_error", "severity": "blocking", "ok": False, "message": message}],
        "review_payload": {"parse_error": parse_error, "filename": filename},
    }


def create_run(
    dsn,
    *,
    uploaded_by,
    filename,
    raw_bytes,
    content_type,
):
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    byte_size = len(raw_bytes)

    # Parse by content_type: .xlsm via openpyxl (temp file), .json via the DataverseExport parser.
    # ANY parse failure becomes a GOVERNED rejected envelope (a persisted run + blocking finding),
    # never an uncaught 500 -- so a malformed upload is still recorded and surfaced to the PM.
    payload = None
    parse_error = None
    try:
        if content_type == "json":
            payload = parse_json_payload(raw_bytes)
        else:
            with tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False) as tf:
                tf.write(raw_bytes)
                tmp_path = pathlib.Path(tf.name)
            try:
                payload = extract_workbook(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
    except Exception as exc:  # any parse failure -> governed rejected envelope (below)
        parse_error = str(exc)

    if parse_error is not None:
        return _create_rejected_parse_envelope(
            dsn, uploaded_by=uploaded_by, filename=filename, content_type=content_type,
            raw_bytes=raw_bytes, sha256=sha256, byte_size=byte_size, parse_error=parse_error,
        )

    project_number = payload.project.project_number
    source_format = classify(payload)
    # n4_defaulted is surfaced by the parser when an N4 cell was blank (getattr keeps this
    # forward-compatible if the payload does not carry the flag).
    n4_defaulted = bool(getattr(payload, "n4_defaulted", False))
    findings = validate_payload(payload, source_format=source_format, n4_defaulted=n4_defaulted)

    if source_format in ("flat_quote", "unsupported"):
        pre_status = "rejected"
    else:
        pre_status = None

    payload_json = json.dumps(dataclasses.asdict(payload), default=str)

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


def create_run_native(dsn, *, uploaded_by, envelope):
    """Native (estimator) catalog-only envelope intake. Pivots to a flat IntakePayload, persists an
    intake_run (source_format='native') with canonical==review==pivoted and the raw envelope in the
    estimate_envelope_json sidecar. approve_run materializes it unchanged. Fail-closed: any blocking
    finding -> a GOVERNED rejected run with NO domain writes (mirrors _create_rejected_parse_envelope)."""
    findings = validate_envelope(envelope)
    blocking = [f for f in findings if f.severity == "blocking" and not f.ok]
    raw_json = json.dumps(envelope, default=str)
    pn = envelope.get("project_number") or ("UNRESOLVED:" + str(envelope.get("envelope_id") or "native"))[:200]
    # identity provenance cols are TOP-LEVEL envelope fields -> safe even for a malformed (rejected) envelope
    ev_id, qv = envelope.get("envelope_id"), envelope.get("quote_version")
    sdid, srid = envelope.get("source_draft_id"), envelope.get("source_revision_id")

    def _finding_rows(cur, run_id, version):
        for f in findings:
            cur.execute(
                "insert into ops.intake_validation_findings"
                " (run_id, payload_version, severity, code, ok, message, diagnostic_detail)"
                " values (%s,%s,%s,%s,%s,%s,%s)",
                (run_id, version, f.severity, f.code, f.ok, f.message, f.diagnostic_detail))

    if blocking:
        # R1-4: governed rejected run — NO advisory lock, NO domain writes, and NO strict pivot/hash
        # (they dereference required fields and would KeyError on a malformed envelope). canonical/review
        # = '{}' (not approvable); content_hash NULL (a reject never takes the idempotency index).
        # D1 Codex P2#2: quote_version=NULL for rejected rows — a rejected run is an audit record, not
        # a version anchor. NULL is excluded from uq_intake_runs_proj_quote_version_native (partial index
        # predicate: ... AND quote_version IS NOT NULL), so retrying the same malformed/rejected envelope
        # always produces a governed reject instead of a UniqueViolation/500.
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "insert into ops.intake_runs (project_number, source_format, status, conflict_kind,"
                " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
                " uploaded_by, envelope_id, quote_version, content_hash, source_draft_id,"
                " source_revision_id, estimate_envelope_json) values"
                " (%s,'native'::ops.intake_source_format,'rejected','none',%s,%s,'{}'::jsonb,'{}'::jsonb,"
                " %s,%s,NULL,NULL,%s,%s,%s::jsonb) returning id",
                (pn, NATIVE_SCHEMA_VERSION, NATIVE_PARSER_VERSION, str(uploaded_by),
                 ev_id, sdid, srid, raw_json))
            run_id = str(cur.fetchone()[0])
            _finding_rows(cur, run_id, 1)
            conn.commit()
        return {"run_id": run_id, "status": "rejected", "conflict_kind": "none", "source_format": "native",
                "findings": [{"code": f.code, "severity": f.severity, "ok": f.ok, "message": f.message} for f in findings]}

    # happy path: validate_envelope guaranteed catalog completeness, so the strict pivot/hash are safe now.
    content_hash = recompute_content_hash(envelope)
    # Compute pivot_dict ONCE — used for both the JSON payload and economic reconciliation.
    pivot_dict = pivot_to_intake_payload(envelope)
    pivoted_json = json.dumps(pivot_dict, default=str)
    # Economic reconciliation: run the shared validate_payload on the pivoted payload.
    # source_format='native' is now accepted (Change 1); numeric money from the pivot makes
    # adjusted_total arithmetic clean. Findings: any blocking econ mismatch -> unapprovable
    # (blocked_findings), mirroring workbook intake — NOT a hard reject.
    econ_findings = validate_payload(_payload_from_dict(pivot_dict), source_format="native", n4_defaulted=False)
    all_findings = findings + econ_findings

    def _all_finding_rows(cur, run_id, version):
        for f in all_findings:
            cur.execute(
                "insert into ops.intake_validation_findings"
                " (run_id, payload_version, severity, code, ok, message, diagnostic_detail)"
                " values (%s,%s,%s,%s,%s,%s,%s)",
                (run_id, version, f.severity, f.code, f.ok, f.message, f.diagnostic_detail))

    try:
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select pg_advisory_xact_lock(hashtext(%s))", (pn,))
            project_id, conflict_kind = _classify_conflict(cur, pn)
            status = "revision_blocked" if conflict_kind != "none" else "parsed"
            if status == "parsed":
                cur.execute(
                    "update ops.intake_runs set status='superseded'::ops.intake_run_status, updated_at=now()"
                    " where project_number=%s and status in ('parsed'::ops.intake_run_status,'reviewing'::ops.intake_run_status)",
                    (pn,))
            cur.execute(
                "insert into ops.intake_runs (project_number, project_id, source_format, status, conflict_kind,"
                " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
                " uploaded_by, envelope_id, quote_version, content_hash, source_draft_id,"
                " source_revision_id, estimate_envelope_json) values"
                " (%s,%s,'native'::ops.intake_source_format,%s::ops.intake_run_status,%s::ops.intake_conflict_kind,"
                " %s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s::jsonb) returning id",
                (pn, project_id, status, conflict_kind, NATIVE_SCHEMA_VERSION, NATIVE_PARSER_VERSION,
                 pivoted_json, pivoted_json, str(uploaded_by), ev_id, qv, content_hash, sdid, srid, raw_json))
            run_id = str(cur.fetchone()[0])
            _all_finding_rows(cur, run_id, 1)
            conn.commit()
    except psycopg.errors.UniqueViolation as exc:
        # C6-RESOLVED: uq_intake_runs_content_hash_native no longer exists; idempotency is
        # anchored on (project_number, quote_version) via uq_intake_runs_proj_quote_version_native.
        if ("uq_intake_one_active" in str(exc)
                or "uq_intake_runs_proj_quote_version_native" in str(exc)):
            raise ActiveRunExists("An active/duplicate native run already exists for " + repr(pn)) from exc
        raise
    return {"run_id": run_id, "status": status, "conflict_kind": conflict_kind, "source_format": "native",
            "findings": [{"code": f.code, "severity": f.severity, "ok": f.ok, "message": f.message} for f in all_findings],
            "review_payload": json.loads(pivoted_json)}


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

            # Return ONLY the CURRENT review-version findings (match approve_run's filter). Prior
            # versions stay in the table as history but must NOT surface, else a blocker the PM
            # already resolved in v2 keeps the UI Approve button disabled via a stale v1 row.
            cur.execute(
                "select code, severity, ok, message"
                "  from ops.intake_validation_findings"
                " where run_id = %s and payload_version = %s"
                " order by created_at",
                (run_id, review_payload_version),
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

def reject_run(dsn, run_id, *, reason):
    """Reject an active intake run (parsed or reviewing only).

    Sets status='rejected' and records the reason.  Returns the updated run dict.
    Raises KeyError if the run is unknown; raises ValueError if the run is not in
    an active status (parsed/reviewing), so the route can return 409.
    """
    _ACTIVE_STATUSES = {"parsed", "reviewing"}

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select status from ops.intake_runs where id = %s",
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError("run not found: " + repr(run_id))
            status = row[0]
            if status not in _ACTIVE_STATUSES:
                raise ValueError(
                    "reject_run only allowed on parsed/reviewing runs; "
                    "run " + repr(run_id) + " has status " + repr(status)
                )
            cur.execute(
                "update ops.intake_runs"
                " set status = %s::ops.intake_run_status,"
                "     rejected_reason = %s,"
                "     updated_at = now()"
                " where id = %s",
                ("rejected", reason, run_id),
            )
        conn.commit()

    return get_run(dsn, run_id)
