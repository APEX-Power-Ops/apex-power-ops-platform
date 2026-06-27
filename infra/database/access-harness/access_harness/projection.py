"""access_harness.projection -- pure logic, no DB connection required.

Defines the Access-table -> tcc-table projection map and, critically, the
FORBIDDEN-key guard that makes a direct Access-surrogate -> tcc.tmt_frames.id
join STRUCTURALLY IMPOSSIBLE.

Why the guard exists (do not re-derive)
---------------------------------------
tcc.tmt_frames.id is a DENSE RE-SEQUENCED surrogate.  It does NOT preserve the
Access Breaker_TMTFrameSizes.ID, nor any child FrameSizeID.  Therefore a direct
join of the form

    <access surrogate>  <->  tmt_frames.id

compares two unrelated integer spaces and is provenance-DISHONEST (this exact
anti-join mistake was made and fixed once already; this guard makes it
impossible to reintroduce).

The ONLY provenance-honest, style-mediated path is:

    Access StyleID
      -> brk_{class}_styles.source_id
      -> brk_{class}_styles.id
      -> tmt_frames.breaker_style_id

after which frames are matched WITHIN a style on natural attributes.
`resolve_frame_join` returns exactly that class-specific chain.

Forbidden-key predicate (assert_key_allowed)
---------------------------------------------
A pairing (access_col, tcc_col) is FORBIDDEN iff BOTH hold:

  1. The tcc side, after normalisation (lowercased, single/double quotes and
     surrounding whitespace stripped from each dotted segment), equals
     'tmt_frames.id'.  This accepts both the bare form 'tmt_frames.id' and the
     quoted form "'tmt_frames'.'id'".

  2. The access side is a RAW SURROGATE -- i.e. the final dotted segment of the
     access column (its actual column name), lowercased, is exactly 'id' or
     'framesizeid'.  This catches the frame's own Breaker_TMTFrameSizes.ID and
     ANY child <table>.FrameSizeID (Amps / Settings / Curves / ThermalTripAdj).

Natural-attribute keys (FrameDesc, TripAmp, ...) never satisfy clause 2, so the
style-mediated path is unaffected.  Mapping a raw surrogate to a NON-frame-id
target (e.g. a provenance source_id column) never satisfies clause 1, so it is
allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class ForbiddenKeyError(Exception):
    """Raised when a direct Access-surrogate -> tmt_frames.id join is attempted.

    Such a join compares the Access ID/FrameSizeID integer space against the
    dense re-sequenced tcc.tmt_frames.id surrogate -- they are unrelated.  The
    only honest path is style-mediated (see resolve_frame_join).
    """


# ---------------------------------------------------------------------------
# Projection map
# ---------------------------------------------------------------------------

# Valid tcc_build_kind values.
_BUILD_KINDS = {'1:1_load', 'computed', 'derived'}

# The verbatim Access-table -> tcc projection definitions.  Each entry is a
# (tcc_table, col_map, tcc_build_kind) triple.
_TABLE_DEFS: Dict[str, tuple] = {
    'Breaker_TMTFrameSizes': (
        'tmt_frames',
        {},
        '1:1_load',
    ),
    'Breaker_TMTFrameAmps': (
        'tmt_amps',
        {'TripAmp': 'rating'},
        '1:1_load',
    ),
    'Breaker_TMTFrameSettings': (
        'tmt_settings',
        {},
        '1:1_load',
    ),
    'Breaker_TMTFrameCurves': (
        'tmt_curves',
        {'Class': 'class', 'Time': 'time_sec', 'Amps': 'current_amp'},
        'computed',
    ),
    'Breaker_TMTThermalTripAdj': (
        'tmt_thermal_adj',
        {'Adjustment': 'adjustment'},
        'derived',
    ),
}


@dataclass(frozen=True)
class ProjectionMap:
    """One Access-table -> tcc-table projection.

    Attributes
    ----------
    access_table : str
        Source Microsoft Access table name (verbatim).
    tcc_table : str
        Destination tcc table name.
    col_map : dict
        Access column name -> tcc column name.  May be empty for tables whose
        column correspondence is established elsewhere (e.g. 1:1 loads keyed on
        natural attributes).
    tcc_build_kind : str
        One of '1:1_load' | 'computed' | 'derived' -- how the tcc table is
        produced from Access.
    """

    access_table: str
    tcc_table: str
    col_map: Dict[str, str] = field(default_factory=dict)
    tcc_build_kind: str = '1:1_load'

    @classmethod
    def for_table(cls, access_table: str) -> 'ProjectionMap':
        """Build the ProjectionMap for a known Access table.

        Raises
        ------
        KeyError
            If access_table is not one of the defined projection tables.
        """
        if access_table not in _TABLE_DEFS:
            raise KeyError(
                f'No projection defined for Access table {access_table!r}'
            )
        tcc_table, col_map, build_kind = _TABLE_DEFS[access_table]
        # Copy col_map so callers cannot mutate the module-level definition.
        return cls(
            access_table=access_table,
            tcc_table=tcc_table,
            col_map=dict(col_map),
            tcc_build_kind=build_kind,
        )


# ---------------------------------------------------------------------------
# Style-mediated join plan
# ---------------------------------------------------------------------------

# Breaker classes that have a brk_{class}_styles table.
_BREAKER_CLASSES = {'MCCB', 'ICCB', 'PCB'}


@dataclass(frozen=True)
class JoinPlan:
    """The provenance-honest, style-mediated chain to reach tmt_frames.

    `chain` is an ordered list of join hops, class-specific:
        ['StyleID',
         'brk_{class}_styles.source_id',
         'brk_{class}_styles.id',
         'tmt_frames.breaker_style_id']
    """

    breaker_class: str
    chain: List[str]


def resolve_frame_join(pm: ProjectionMap, breaker_class: str) -> JoinPlan:
    """Return the class-specific, style-mediated chain to reach tmt_frames.

    This is the ONLY sanctioned way to relate an Access frame row to a
    tcc.tmt_frames row.  It never touches tmt_frames.id directly; it routes
    through breaker_style_id via the per-class style table's source_id ->
    id provenance hop.

    Parameters
    ----------
    pm : ProjectionMap
        The projection for the Access frame table (carried for symmetry with
        the rest of the API; the chain is determined by breaker_class).
    breaker_class : str
        One of 'MCCB' | 'ICCB' | 'PCB'.

    Raises
    ------
    ValueError
        If breaker_class is not a known breaker class.
    """
    if breaker_class not in _BREAKER_CLASSES:
        raise ValueError(
            f'Unknown breaker_class {breaker_class!r}; '
            f'expected one of {sorted(_BREAKER_CLASSES)}'
        )
    lc = breaker_class.lower()
    chain = [
        'StyleID',
        f'brk_{lc}_styles.source_id',
        f'brk_{lc}_styles.id',
        'tmt_frames.breaker_style_id',
    ]
    return JoinPlan(breaker_class=breaker_class, chain=chain)


# ---------------------------------------------------------------------------
# FORBIDDEN-key guard
# ---------------------------------------------------------------------------

# Lowercased access column-name leaves that are RAW SURROGATES.
_SURROGATE_LEAVES = {'id', 'framesizeid'}

# The single forbidden tcc target, normalised.
_FORBIDDEN_TCC_TARGET = 'tmt_frames.id'


def _normalize_ref(ref: str) -> str:
    """Lowercase a dotted column ref and strip quotes/whitespace per segment.

    'tmt_frames.id'        -> 'tmt_frames.id'
    "'tmt_frames'.'id'"    -> 'tmt_frames.id'
    '  TMT_Frames . ID '   -> 'tmt_frames.id'
    """
    segments = ref.split('.')
    cleaned = []
    for seg in segments:
        seg = seg.strip().strip('"').strip("'").strip()
        cleaned.append(seg.lower())
    return '.'.join(cleaned)


def _access_leaf(access_col: str) -> str:
    """Return the lowercased final dotted segment (the column name) of access_col.

    'Breaker_TMTFrameSizes.ID' -> 'id'
    'Breaker_TMTFrameAmps.FrameSizeID' -> 'framesizeid'
    'Breaker_TMTFrameAmps.TripAmp' -> 'tripamp'
    """
    return _normalize_ref(access_col).split('.')[-1]


def assert_key_allowed(pm: ProjectionMap, access_col: str, tcc_col: str) -> None:
    """Raise ForbiddenKeyError for any direct Access-surrogate -> tmt_frames.id join.

    The pairing is FORBIDDEN iff BOTH:
      1. the tcc side normalises to 'tmt_frames.id', AND
      2. the access side's column leaf is a raw surrogate ('id' or
         'framesizeid').

    All other pairings (natural attributes, or a surrogate routed to a
    non-frame-id target) are allowed and return None.

    Parameters
    ----------
    pm : ProjectionMap
        The projection in effect (carried for context / future per-table
        policy; the predicate itself is table-agnostic by design so it cannot
        be sidestepped by mislabelling the table).
    access_col : str
        The Access side of the proposed join, e.g. 'Breaker_TMTFrameSizes.ID'.
    tcc_col : str
        The tcc side, e.g. 'tmt_frames.id' or "'tmt_frames'.'id'".

    Raises
    ------
    ForbiddenKeyError
        If the pairing is a direct surrogate -> tmt_frames.id join.
    """
    if _normalize_ref(tcc_col) != _FORBIDDEN_TCC_TARGET:
        return  # target is not tmt_frames.id -- nothing to forbid
    if _access_leaf(access_col) not in _SURROGATE_LEAVES:
        return  # access side is a natural attribute -- allowed

    raise ForbiddenKeyError(
        f'Direct Access-surrogate join is forbidden: '
        f'{access_col!r} -> {tcc_col!r}. '
        f'tcc.tmt_frames.id is a dense re-sequenced surrogate that does NOT '
        f'preserve the Access ID/FrameSizeID; this join compares unrelated '
        f'integer spaces. Use the style-mediated path via resolve_frame_join '
        f'(StyleID -> brk_{{class}}_styles.source_id -> brk_{{class}}_styles.id '
        f'-> tmt_frames.breaker_style_id).'
    )
