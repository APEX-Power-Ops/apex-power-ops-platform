"""access_harness.checksum -- pure logic, no DB connection required.

Deterministic full-row checksum + multiset diff for fidelity validation.

A structurally perfect 1:1 mirror must checksum-match byte-identically on
both the Access source side and the Postgres (tcc) side.  The multiset diff
is the fallback used when a table has no unique key, so it counts rows by
canonical value rather than by key.

Determinism rules (see canonical_row):
  - The per-cell encoding is INJECTIVE: each field is emitted as a typed,
    length-prefixed token so that no data content can shift a field boundary
    and no text value can impersonate a SQL NULL.
        NULL / None  -> the literal token "N"
        non-null     -> "V" + len(enc) + ":" + enc
    where enc is the value's canonical string form (below).  Two distinct
    rows therefore always produce distinct canonical strings (within a fixed
    column count), so the separator collision and sentinel-impersonation
    classes are both eliminated.
  - Value canonicalization (enc) is by the value's *nature*, because str()
    is driver-unstable across pyodbc builds:
        datetime / date     -> .isoformat()        (byte-stable)
        decimal.Decimal     -> format(d.normalize(), 'f')   (scale-normalized:
                               Decimal('1.50') == Decimal('1.5'))
        bytes / bytearray   -> .hex()              (byte-stable)
        float-typed column  -> format(value, '.17g')  (0.1+0.2 == 0.300...004)
        everything else     -> str(value)
  - Tokens joined in their given (fixed) order with "\x01".
"""
import datetime
import decimal
import hashlib
from collections import Counter
from typing import Iterable

from access_harness.typemap import ColumnType

# Tag for a NULL / None cell.  A bare "N" token -- a real value is always
# emitted as a "V"-tagged, length-prefixed token, so the two can never collide.
_NULL_TOKEN = "N"
# Column separator -- cosmetic now that each token is length-prefixed and
# self-delimiting; retained for readability of the canonical string.
_COL_SEP = "\x01"
# pg_type values that should be formatted with full float precision.
_FLOAT_PG_TYPES = frozenset({"double precision", "real"})


def _encode_value(value: object, col_type: ColumnType) -> str:
    """Render one non-null value to its canonical, driver-stable string form.

    Canonicalizes by the value's nature so the result is byte-stable across
    pyodbc / driver builds (str() is not).
    """
    # datetime / date -> ISO 8601 (stable; str() varies on tz / microseconds).
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    # Decimal -> scale-normalized fixed form: Decimal('1.50') == Decimal('1.5').
    # normalize() collapses trailing-zero scale; format(..., 'f') avoids the
    # exponential form normalize() can yield for large integers (e.g. 1E+1).
    if isinstance(value, decimal.Decimal):
        return format(value.normalize(), "f")
    # bytes / bytearray -> lowercase hex (stable; str() yields a b'...' repr).
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    # float-typed column -> '.17g' round-trips an IEEE-754 double to a
    # byte-stable representation: 0.1+0.2 and 0.30000000000000004 match.
    if col_type.pg_type in _FLOAT_PG_TYPES:
        return format(value, ".17g")
    return str(value)


def _canonical_cell(value: object, col_type: ColumnType) -> str:
    """Render one cell to its INJECTIVE, typed, length-prefixed token.

    None        -> "N"
    non-null    -> "V" + len(enc) + ":" + enc

    The length prefix makes the token self-delimiting, so no field's content
    can shift a boundary; the V/N tag means no text value can impersonate NULL.
    """
    if value is None:
        return _NULL_TOKEN
    enc = _encode_value(value, col_type)
    return f"V{len(enc)}:{enc}"


def canonical_row(row: tuple, col_types: list[ColumnType]) -> str:
    """Return a deterministic, injective canonical string for one row.

    col_types aligns positionally with row.  Raises ValueError on an
    arity mismatch (len(row) != len(col_types)) so a misaligned compare
    fails loudly rather than silently truncating via zip().
    """
    if len(row) != len(col_types):
        raise ValueError(
            f"canonical_row arity mismatch: {len(row)} values vs "
            f"{len(col_types)} col_types"
        )
    return _COL_SEP.join(
        _canonical_cell(value, col_type) for value, col_type in zip(row, col_types)
    )


def table_checksum(rows: Iterable[tuple], col_types: list[ColumnType]) -> str:
    """Return the sha256 hex digest over ALL rows.

    Each row is canonicalized, the canonical strings are SORTED (so the
    checksum is row-order-independent), joined with "\n", and hashed.
    Deterministic and order-independent.
    """
    canon = sorted(canonical_row(row, col_types) for row in rows)
    joined = "\n".join(canon)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def multiset_diff(left: Counter, right: Counter) -> dict:
    """Compare two Counters (Access vs tcc) key by key.

    For every key present in EITHER Counter, emit:
        {key: {'access': left[k], 'tcc': right[k], 'delta': left[k]-right[k]}}

    Policy: keys with equal counts (delta == 0) are OMITTED -- the diff
    reports only discrepancies, so an empty dict means the multisets match.
    Counter[missing_key] yields 0, so keys present on only one side are
    reported with the absent side as 0.
    """
    out: dict = {}
    for key in set(left) | set(right):
        a = left[key]
        b = right[key]
        if a == b:
            continue
        out[key] = {"access": a, "tcc": b, "delta": a - b}
    return out
