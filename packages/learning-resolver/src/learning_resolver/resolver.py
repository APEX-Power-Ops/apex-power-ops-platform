"""Hybrid contextual resource resolver over learning_dev. Read-only."""
from .db import connect
from .models import ResolvedResource

_CURATED_BASE = 1000.0
_SECTION_BASE = 500.0


def _apparatus_type_ids(conn, section: str) -> list[str]:
    rows = conn.execute(
        "select distinct apparatus_type_id from neta_procedures "
        "where section_number = %(s)s and apparatus_type_id is not null",
        {"s": section},
    ).fetchall()
    return [str(r[0]) for r in rows]


def _curated(conn, apt_ids: list[str]) -> list[ResolvedResource]:
    if not apt_ids:
        return []
    rows = conn.execute(
        """
        select atr.resource_type, atr.is_primary, atr.is_mandatory, atr.display_order,
               atr.study_content_id, atr.neta_procedure_id, atr.resource_url, atr.resource_name,
               sc.title as sc_title, sc.slug as sc_slug, sc.summary as sc_summary,
               sc.certification_level as sc_level,
               np.title as np_title, np.section_number as np_section
        from apparatus_type_resources atr
        left join study_content sc on sc.id = atr.study_content_id
        left join neta_procedures np on np.id = atr.neta_procedure_id
        where atr.apparatus_type_id = any(%(ids)s) and atr.is_active
        order by atr.is_primary desc, atr.is_mandatory desc, atr.display_order asc nulls last
        """,
        {"ids": apt_ids},
    ).fetchall()
    out: list[ResolvedResource] = []
    for i, r in enumerate(rows):
        (rtype, is_primary, is_mandatory, display_order, sc_id, np_id, url, rname,
         sc_title, sc_slug, sc_summary, sc_level, np_title, np_section) = r
        if sc_id is not None:
            title, ref, level = sc_title, {"kind": "study_content", "id": str(sc_id),
                                           "slug": sc_slug, "summary": sc_summary}, sc_level
        elif np_id is not None:
            title, ref, level = np_title, {"kind": "neta_procedure", "section": np_section}, None
        else:
            title, ref, level = (rname or "Linked resource"), {"kind": "url", "url": url}, None
        score = (_CURATED_BASE + (100 if is_primary else 0) + (50 if is_mandatory else 0)
                 - (display_order or 0))
        out.append(ResolvedResource(
            resource_type=rtype, title=title or "Untitled", source="curated", reference=ref,
            is_primary=bool(is_primary), is_mandatory=bool(is_mandatory), cert_level=level,
            score=float(score), why="curated resource for this apparatus type",
        ))
    return out


def _section_match(conn, section: str, exclude_sc_ids: set[str]) -> list[ResolvedResource]:
    rows = conn.execute(
        """
        select sc.id, sc.title, sc.slug, sc.summary, sc.certification_level,
               (sc.neta_section_primary = %(s)s) as primary_hit
        from study_content sc
        where (sc.neta_section_primary = %(s)s or %(s)s = any(sc.neta_sections_secondary))
          and sc.is_active and sc.status = 'published'
        order by (sc.neta_section_primary = %(s)s) desc, sc.title asc
        """,
        {"s": section},
    ).fetchall()
    out: list[ResolvedResource] = []
    for sc_id, title, slug, summary, level, primary_hit in rows:
        if str(sc_id) in exclude_sc_ids:
            continue
        score = _SECTION_BASE + (50 if primary_hit else 0)
        out.append(ResolvedResource(
            resource_type="study_content", title=title or "Untitled", source="section_match",
            reference={"kind": "study_content", "id": str(sc_id), "slug": slug, "summary": summary},
            cert_level=level, score=float(score),
            why=("NETA " + section + " primary-section study content") if primary_hit
                 else ("NETA " + section + " related (secondary) study content"),
        ))
    return out
