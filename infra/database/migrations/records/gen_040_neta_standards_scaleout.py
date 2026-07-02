#!/usr/bin/env python3
"""Generate 040_neta_standards_scaleout.sql — make the remaining datasheets standard-aware.

MTS-accommodation Chip B SCALE-OUT. The pilot (039) proved the v2 shape on ats_liquid_xfmr_v1;
this applies it to every other standard-shared datasheet. Per sheet:

  * field_schema.neta_standards = ["ats","mts"]   (or ["ats"] if the sheet's NETA section has no MTS)
  * each section.neta_covers : flat list  ->  {"ats":[...], "mts":[...]}
  * each section.standards   : ["ats","mts"]  (the section-level flag; default both)

MTS coverage is authored automatically from the seeded neta_test_items.mts and the sheet's EXISTING
ATS coverage, with two placement rules (no new sections):
  - MTS visual/mechanical items -> the sheet's visual-mechanical section (the one holding the most
    ATS "A" refs) — matches how ATS VM items already cluster.
  - MTS electrical items -> the section of the best text-matching ATS electrical item; if none,
    fall back to 'advanced_diagnostics' (if present), else the section holding the most ATS "B" refs.

Placement is a UX nicety; COMPLETENESS is enforced by the per-standard coverage invariant in
test_040 (every MTS item covered, zero phantom). ats_liquid_xfmr_v1 is EXCLUDED (already v2 via 039).

Read-live in-place patch (mirrors 020/039). Run AFTER the full chain incl. 020/021/022/039:
  uv run --no-project --with "psycopg[binary]" python gen_040_neta_standards_scaleout.py
"""
import json
import os
import re

import psycopg

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "040_neta_standards_scaleout.sql")
OUT_DOWN = os.path.join(HERE, "040_neta_standards_scaleout_down.sql")
DSN = _dbtest.require_dsn()
EXCLUDE = {"ats_liquid_xfmr_v1"}  # already standard-aware (039 pilot)

_STOP = {"the", "of", "a", "an", "and", "or", "to", "in", "on", "for", "with", "at", "by",
         "be", "is", "are", "as", "each", "all", "per", "shall", "test", "tests", "perform"}


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", str(s).lower())


def toks(s):
    return {w for w in norm(s).split() if w not in _STOP and len(w) > 2}


def parse_section(ref):
    # "7.6.1.3.B.2" -> "7.6.1.3"; "7.4.A.10" -> "7.4"
    m = re.match(r"^(.*)\.(?:A|B)\.\d+$", ref)
    return m.group(1) if m else None


def best_section(mts_desc, ats_pool):
    # ats_pool: list of (norm_desc, token_set, section). exact-norm first, else best Jaccard >= 0.5
    nd = norm(mts_desc)
    for d, _, sec in ats_pool:
        if d == nd:
            return sec
    mt = toks(mts_desc)
    if not mt:
        return None
    best, bj = None, 0.0
    for _, at, sec in ats_pool:
        if not at:
            continue
        j = len(mt & at) / len(mt | at)
        if j > bj:
            best, bj = sec, j
    return best if bj >= 0.5 else None


def build(code, fs, c):
    fs = dict(fs)
    sections = [dict(s) for s in fs["sections"]]
    # ATS coverage already on the sheet (flat lists)
    ref_section = {}
    a_count, b_count = {}, {}
    for s in sections:
        for r in (s.get("neta_covers") or []):
            ref_section[r] = s["key"]
            if ".A." in r:
                a_count[s["key"]] = a_count.get(s["key"], 0) + 1
            elif ".B." in r:
                b_count[s["key"]] = b_count.get(s["key"], 0) + 1
    neta_sections = sorted({ps for r in ref_section if (ps := parse_section(r))})
    vm_section = max(a_count, key=a_count.get) if a_count else sections[1]["key"]
    keys = {s["key"] for s in sections}
    elec_fallback = ("advanced_diagnostics" if "advanced_diagnostics" in keys
                     else (max(b_count, key=b_count.get) if b_count else vm_section))

    rows = c.execute(
        "select p.section, ti.standard, ti.category, ti.item_number, ti.description "
        "from records.neta_test_items ti join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = any(%s) and ti.category in ('visual_mechanical','electrical')",
        (neta_sections,)
    ).fetchall()
    ats_elec, mts_items = [], []   # ats_elec: (norm,tokens,section); mts_items: (ref,cat,desc)
    for sec, std, cat, num, desc in rows:
        letter = "A" if cat == "visual_mechanical" else "B"
        ref = f"{sec}.{letter}.{num}"
        if std == "ats":
            if cat == "electrical":
                ats_elec.append((norm(desc), toks(desc), ref_section.get(ref, elec_fallback)))
        else:
            mts_items.append((ref, cat, desc))

    mts_cover = {}
    for ref, cat, desc in mts_items:
        if cat == "visual_mechanical":
            sec = vm_section
        else:
            sec = best_section(desc, ats_elec) or elec_fallback
        mts_cover.setdefault(sec, []).append(ref)

    has_mts = bool(mts_items)
    fs["neta_standards"] = ["ats", "mts"] if has_mts else ["ats"]
    out = []
    for s in sections:
        ats = list(s.get("neta_covers") or [])
        s["neta_covers"] = {"ats": ats, "mts": sorted(mts_cover.get(s["key"], []))}
        s.setdefault("standards", fs["neta_standards"])
        out.append(s)
    fs["sections"] = out
    return fs, len(mts_items), has_mts


def upd(code, payload):
    p = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).replace("'", "''")
    return (f"UPDATE records.form_templates SET field_schema = '{p}'::jsonb, updated_at = now()\n"
            f"  WHERE template_code = '{code}' AND is_current;")


def main():
    ups, downs, summary = [], [], []
    with psycopg.connect(DSN) as c:
        codes = [r[0] for r in c.execute(
            "select template_code from records.form_templates "
            "where is_current and form_type='neta_datasheet' order by neta_section"
        ).fetchall()]
        for code in codes:
            if code in EXCLUDE:
                continue
            s0 = c.execute(
                "select field_schema from records.form_templates where template_code=%s and is_current",
                (code,)
            ).fetchone()[0]
            s0 = json.loads(s0) if isinstance(s0, str) else s0
            if isinstance((s0.get("sections") or [{}])[-1].get("neta_covers"), dict):
                continue  # already v2
            v2, nmts, has_mts = build(code, s0, c)
            ups.append(upd(code, v2))
            downs.append(upd(code, s0))
            summary.append((code, nmts, "ats+mts" if has_mts else "ats-only"))

    head = ["-- ============================================================================="
            , "-- Records MTS-accommodation Chip B SCALE-OUT — standard-aware datasheets.",
            "-- GENERATED by gen_040_neta_standards_scaleout.py — do not edit by hand.",
            "-- neta_covers list -> {ats,mts} map; +neta_standards; +standards tag. MTS coverage",
            "-- auto-authored from neta_test_items.mts (VM->vm section; electrical->text-matched).",
            "-- Excludes ats_liquid_xfmr_v1 (039). Read-live patch; reversible _down.",
            "-- =============================================================================",
            "BEGIN;", "SET client_encoding TO 'UTF8';", ""]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(head) + "\n\n".join(ups) + "\n\nCOMMIT;\n")
    dhead = ["-- DOWN for 040 — restore each sheet's pre-040 (flat neta_covers) field_schema.",
             "BEGIN;", "SET client_encoding TO 'UTF8';", ""]
    with open(OUT_DOWN, "w", encoding="utf-8") as fh:
        fh.write("\n".join(dhead) + "\n\n".join(downs) + "\n\nCOMMIT;\n")

    print(f"wrote {OUT} ({len(ups)} sheets)")
    for code, nmts, kind in summary:
        print(f"  {code:28} mts_items={nmts:3} {kind}")


if __name__ == "__main__":
    main()
