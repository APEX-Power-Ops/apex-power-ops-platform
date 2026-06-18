"""The review proposal: classify proposed values against a template's instrument_import targets.

- mapped:   a proposed value whose field_key is a declared instrument_import control target.
- unmapped: a proposed value with no matching target (a mapping/template-drift signal - surfaced, never
            silently written).
- pending:  declared instrument_import targets that no reading filled (partial fill).

Nothing writes here; this drives the review gate (spec 14, section 8).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from records_import.proposal import ProposedValue


@dataclass
class Proposal:
    mapped: list[ProposedValue] = field(default_factory=list)
    unmapped: list[ProposedValue] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


def _instrument_target_keys(field_schema: dict) -> set[str]:
    """Every fillable control tag in the schema's instrument_import sections, as field_keys.

    Table cells -> "<section>.<row>.<column>" (the 'tap' column is a row qualifier, not a value target);
    `fields` controls -> "<section>.<tag>".
    """
    keys: set[str] = set()
    for s in field_schema.get("sections", []):
        if s.get("capture_mode") != "instrument_import":
            continue
        sk = s["key"]
        if s.get("kind") == "table":
            tbl = s.get("table", {})
            rows = [r["key"] for r in tbl.get("row_dim", {}).get("rows", [])]
            cols = [c["tag"] for c in tbl.get("columns", []) if c.get("tag") not in (None, "tap")]
            for r in rows:
                for c in cols:
                    keys.add(f"{sk}.{r}.{c}")
        else:
            for f in s.get("fields", []):
                if f.get("tag"):
                    keys.add(f"{sk}.{f['tag']}")
    return keys


def build_proposal(proposed: list[ProposedValue], field_schema: dict) -> Proposal:
    targets = _instrument_target_keys(field_schema)
    p = Proposal()
    filled: set[str] = set()
    for v in proposed:
        if v.field_key in targets:
            p.mapped.append(v)
            filled.add(v.field_key)
        else:
            p.unmapped.append(v)
    p.pending = sorted(targets - filled)
    return p
