from __future__ import annotations
"""Thin, value-free wrappers over the ops 009 recognition-bridge functions.

Sole-writer discipline: these call ops.attest_apparatus_complete / approve_and_recognize /
reverse_recognition / revoke_completion_attestation and translate DB exceptions into a small
set of typed, VALUE-FREE errors (no dollar amounts, no internal text). The API maps these to
generic 400/409; the raw DB message is NEVER surfaced.
"""
import psycopg

class RecognitionError(Exception):
    """Base — message is always a fixed, value-free string."""

class RecognitionInputError(RecognitionError):
    """Bad/zero input: unknown actor, blank reason, out-of-enum clearance. -> API 400."""

class RecognitionConflict(RecognitionError):
    """State conflict: active attestation already exists / already recognized / open recognition. -> API 409."""

class RecognitionStateError(RecognitionError):
    """Ineligible or wrong-state target (not approved, cancelled chain, no active attestation). -> API 409."""

# Stable, value-free substrings emitted by the 009 functions (P0001). Matched on the DB
# message ONLY to CLASSIFY; the surfaced message is always one of the fixed strings below.
# Note: "cannot attest from status" maps to Conflict — it means the apparatus is already
# Complete (a prior attest got there), so a second attest IS a conflict, not a state error.
_CONFLICT_HINTS = ("already recognized", "open recognition", "no longer active",
                   "already revoked", "already has an open recognition",
                   "cannot attest from status")
_STATE_HINTS    = ("not approved", "inactive/cancelled", "cannot attest", "cannot recognize",
                   "no active completion attestation", "not found", "not testing-complete",
                   "basis not frozen", "invalid quote basis")
_INPUT_HINTS    = ("reason required", "unknown actor", "clearances required")

def _classify(exc: psycopg.Error) -> RecognitionError:
    if isinstance(exc, psycopg.errors.UniqueViolation):
        return RecognitionConflict("a conflicting recognition state already exists")
    if isinstance(exc, psycopg.errors.ForeignKeyViolation):
        return RecognitionInputError("invalid input reference")
    msg = (getattr(getattr(exc, "diag", None), "message_primary", None) or str(exc)).lower()
    if any(h in msg for h in _INPUT_HINTS):
        return RecognitionInputError("invalid input")
    if any(h in msg for h in _CONFLICT_HINTS):
        return RecognitionConflict("recognition state conflict")
    if any(h in msg for h in _STATE_HINTS):
        return RecognitionStateError("apparatus not in a valid state for this action")
    # value-free fallback — NEVER str(exc)
    return RecognitionStateError("recognition action rejected")

def _call_scalar(dsn: str, sql: str, params: tuple) -> str:
    try:
        with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
            cur.execute(sql, params)
            return str(cur.fetchone()[0])
    except psycopg.Error as exc:
        raise _classify(exc) from None

def attest_complete(dsn: str, apparatus_id: str, attested_by: str, reason: str) -> str:
    return _call_scalar(dsn, "select ops.attest_apparatus_complete(%s,%s,%s)",
                        (apparatus_id, attested_by, reason))

def recognize(dsn: str, apparatus_id: str, actor: str,
              datasheet_clearance: str, datasheet_ref, cx_clearance: str, cx_ref) -> str:
    return _call_scalar(
        dsn,
        "select ops.approve_and_recognize(%s,%s,%s::ops.obligation_clearance,%s,"
        "%s::ops.obligation_clearance,%s)",
        (apparatus_id, actor, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref))

def reverse(dsn: str, event_id: str, actor: str, reason: str) -> str:
    return _call_scalar(dsn, "select ops.reverse_recognition(%s,%s,%s)", (event_id, actor, reason))

def revoke(dsn: str, attestation_id: str, actor: str, reason: str) -> str:
    return _call_scalar(dsn, "select ops.revoke_completion_attestation(%s,%s,%s)",
                        (attestation_id, actor, reason))
