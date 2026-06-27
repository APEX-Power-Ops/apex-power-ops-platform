"""access_harness.checksum -- pure logic, no DB connection required.

Deterministic full-row checksum + multiset diff for fidelity validation.

A structurally perfect 1:1 mirror must checksum-match byte-identically on
both the Access source side and the Postgres (tcc) side.  The multiset diff
is the fallback used when a table has no unique key, so it counts rows by
canonical value rather than by key.

Determinism rules (see canonical_row):
  - NULL / None  -> a fixed sentinel "\x00NULL", distinct from empty str "".
  - float-typed column (pg_type in {'double precision','real'})
                 -> format(value, '.17g'), so 0.1+0.2 and 0.30000000000000004
                    render identically.
  - everything else -> str(value).
  - columns joined in their given (fixed) order with "\x01" (cannot appear
    in the sentinel).
"""
import hashlib
from collections import Counter
from typing import Iterable

from access_harness.typemap import ColumnType

# Sentinel for a NULL / None cell.  Distinct from the empty string "".
_NULL_SENTINEL = "\x00NULL"
# Column separator -- a byte that cannot appear inside _NULL_SENTINEL prose
# and is extremely unlikely in textual data.
_COL_SEP = "\x01"
# pg_type values that should be formatted with full float precision.
_FLOAT_PG_TYPES = frozenset({"double precision", "real"})


def _canonical_cell(value: object, col_type: ColumnType) -> str:
    """Render one cell to its canonical, deterministic string form."""
    if value is None:
        return _NULL_SENTINEL
    if col_type.pg_type in _FLOAT_PG_TYPES:
        # '.17g' round-trips an IEEE-754 double to a byte-stable shortest-ish
        # representation: 0.1+0.2 and 0.30000000000000004 both render the same.
        return format(value, ".17g")
    return str(value)


def canonical_row(row: tuple, col_types: list[ColumnType]) -> str:
    """Return a deterministic canonical string for one row.

    col_types aligns positionally with row.  Columns are joined in their
    given (fixed) order with _COL_SEP.
    """
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
