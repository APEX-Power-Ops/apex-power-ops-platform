# Codex packet — Catalog library curation Phase 2 (reclassify Unknowns + file long-tail + dedup)

- **Queued by:** CC (Claude Code), 2026-06-07
- **Task ref:** #97 (Catalog resource repository — curate)
- **Repo:** `apex-power-ops-platform` (PUBLIC) — **metadata only in git; never commit PDFs/binaries**
- **Builder to reuse/extend:** `.audit_workspace/etap_tcc_sources/catalogs/build_catalog_library.py`
- **Manifest:** `reference/tcc/catalogs/CATALOG-INDEX.csv` (currently **192 rows** after CC purged 6 stray quarantine accidents in commit `a41edace`)
- **Review tree (synced, NOT git):** `C:\Users\jjswe\Resa Power, LLC\RESA Power Ops - Phoenix Files\Technical Data\_NORMALIZED_REVIEW`
- **Workbook mfr vocab (canonical authority):** `reference/tcc/crosswalk/EP_to_ETAP_master_crossref.xlsx` → `Manufacturers` sheet

## Goal

Close the three remaining curation buckets so the library has **zero `Unknown` docs** and the four long-tail manufacturers are filed. CC has already done the identification work — your job is to **audit, apply, dedup, and re-manifest** deterministically, then hand back a closeout.

---

## Bucket A — reclassify the 12 `Unknown` docs (IDs are authoritative; verify, then apply)

All 12 currently sit under `…/Unknown/…` with `canonical_mfr=Unknown, not_in_workbook=Y`. CC identified every one (doc-number conventions + page-text + one web confirm). **Verify each against the PDF before moving** (open page 1–3; confirm the vendor/family), then relocate into `<DeviceClass>/<CanonicalMfr>/<Family>/` and rewrite the manifest row (`canonical_mfr`, `family`, `normalized_relpath`, and re-evaluate `not_in_workbook` — see rule below).

| current file (under `_NORMALIZED_REVIEW/`) | → canonical_mfr | family | device_class | note |
|---|---|---|---|---|
| `Breakers/Unknown/Unclassified/1SDC007600G0201_WP MDGF_12.2024.pdf.pdf` | **ABB** | Ground-fault white paper (MDGF) | Breakers | `1SDC` = ABB doc prefix |
| `Breakers/Unknown/Unclassified/9AKK108467A9440_en_B_BuyLog Section 8_ LV insulated case circuit breakers.pdf` | **ABB** | BuyLog Sec. 8 / ICCB | Breakers | `9AKK` = ABB; **DEDUP vs `rejected-revisit/abb_buylog_08_…` — same doc; keep one (prefer the complete official copy)** |
| `Breakers/Unknown/Unclassified/1010466024-la-3000.pdf` | **Allis-Chalmers** | LA-3000/4000 ACB (1967 IB) | Breakers | legacy vendor — likely `not_in_workbook=Y` |
| `Breakers/Unknown/Unclassified/3aaaef.pdf` | **ITE** | Power Shield SS trip | Breakers/Trip Units | ManualsLib "ITE Power Shield" |
| `Trip Units/Unknown/Selectivity/484019416-Catalogue-Record-Plus-English-7-pdf.pdf` | **General Electric** | Record Plus FD/FE MCCB | Breakers | GE Power Controls line (FD160/FE160) — note: it's a **breaker** catalog, reclass device_class to Breakers |
| `Breakers/Unknown/M-Pact/870643927-ACB-OMEGA.pdf` | **L&T** | Omega ACB | Breakers | **mis-foldered under M-Pact**; DEDUP vs `larsen-toubro/lt-omega-acb.pdf` |
| `Trip Units/Unknown/ComPacT NS/kupdf.net_compact-merlin-gerin-str.pdf` | **Merlin Gerin** | Compact STR trip | Trip Units | complementary to MG batch (keep) |
| `Breakers/Unknown/Unclassified/W1000710.pdf` | **Federal Pioneer** | USR solid-state trip | Trip Units | ⭐ primary source for the §175–180 USR plug-fills; reclass device_class to Trip Units |
| `Trip Units/Unknown/Unclassified/W1001130.pdf` | **Westinghouse** | Pow-R / DS draw-out (I.B. 15012, 1977) | Breakers | **legacy** Westinghouse; reclass device_class to Breakers |
| `Breakers/Unknown/Unclassified/DEA-013C.pdf` | **General Electric** | Power Break II ICCB | Breakers | confirmed via ABB library doc-number `DEA-013C` = "Power Break II – Insulated Case CBs" (GE line, ABB-hosted) |
| `Breakers/Unknown/WHG/ACB WHG Series WH.08ACB0824.pdf` | **Westinghouse** | WHG ACB **(modern licensed)** | Breakers | self-IDs "Westinghouse, since 1886"; **modern Chinese-OEM licensed brand, NOT legacy WH** — set `notes=modern licensed brand` |
| `Breakers/Unknown/Unclassified/MCCB-WH-01-MCCB0924.pdf` | **Westinghouse** | G/F/J MCCB **(modern licensed)** | Breakers | same modern-licensed line as WHG |

**`not_in_workbook` rule:** after assigning canonical_mfr, check it against the workbook `Manufacturers` sheet. Set `not_in_workbook=Y` **only** when the canonical mfr is genuinely absent from that vocab (expect: Allis-Chalmers likely Y; the modern-licensed "Westinghouse" line — flag in `notes` even though "Westinghouse" is in vocab). ABB / GE / ITE / L&T / Merlin Gerin / Federal Pioneer / Westinghouse are all in the workbook (per the gap-pressure table) → `not_in_workbook` blank for those.

After this bucket, the `Unknown/` folders should be **empty → remove them**.

---

## Bucket B — file the 4 long-tail manufacturers + reconcile the recoveries

Source PDFs are staged host-local at `.audit_workspace/catalog_lane/longtail/` (gitignored). Copy the **kept** ones into the review tree under `<DeviceClass>/<CanonicalMfr>/<Family>/` and add manifest rows (`provenance_type=web`, `source_origin=web`, with `source_url`/`retrieved` where known — pull from the staging notes if present, else mark `retrieved=2026-06-06`).

```
fuji-electric/   fuji_acb_bt3_series_…  fuji_acb_dw_series_…  fuji_mccb_elcb_americas_USEH240E   → canonical_mfr=Fuji
ite-bbc-/        ITE_SolidStateTrip_504TestSet…  K-Line_K225-K2000…  MicroVersaTrip_RMS-9_… → canonical_mfr=ITE
larsen-toubro/   lt-cpower-acb-catalogue-2024  lt-dsine-mccb-catalogue  lt-omega-acb           → canonical_mfr=L&T
merlin-gerin/    compact-ns-2011  complementary-technical-info-2007  masterpact-nt-nw  mg-…application-guide → canonical_mfr=Merlin Gerin
rejected-revisit/  abb_buylog_06…  abb_buylog_08…  lt_cpower_acb…  lt_dsine_mccb…  schneider_squared_powerpact_hjl…  siemens_3va_mccb_ul…
```

**Dedup hot-spots (must reconcile, do not double-file):**
1. `rejected-revisit/abb_buylog_08_lv_power_insulated_case_breakers.pdf` **==** Bucket-A `9AKK…BuyLog Section 8` → same doc. Keep ONE under **ABB**.
2. `rejected-revisit/lt_dsine_mccb_catalogue.pdf` **==** `larsen-toubro/lt-dsine-mccb-catalogue.pdf` (same size) → exact dup, keep one.
3. `rejected-revisit/lt_cpower_acb_catalogue.pdf` (1.2 MB) vs `larsen-toubro/lt-cpower-acb-catalogue-2024.pdf` (56 MB) → likely partial vs full; keep the **full** one, drop the partial.
4. `larsen-toubro/lt-omega-acb.pdf` vs Bucket-A `870643927-ACB-OMEGA.pdf` → compare (SHA + page 1); keep one under **L&T**.
5. `rejected-revisit/abb_buylog_06…`, `schneider_squared_powerpact_hjl…`, `siemens_3va_mccb_ul…` → file under ABB / Schneider Electric (Square-D) / Siemens respectively; **dedup against the existing manifest** (Siemens 3VA + Schneider PowerPact families may already be present from Phase 1).

Use SHA-256 + recovered-doc-identity dedup (same policy as the Phase-1 builder).

---

## Constraints (hard)

- **Git:** scoped `git add` of metadata files **only** (`reference/tcc/catalogs/CATALOG-INDEX.csv`, `reference/tcc/catalogs/README.md` if counts change, `reference/tcc/00-MASTER-INDEX.md`). **Never `-A`. Never stage a PDF/binary.** Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **No hard-delete of originals.** Staging PDFs remain in `.audit_workspace/`. If you must remove a superseded review-tree copy during dedup, **move to Recycle Bin** (reversible), not permanent delete.
- **Verified-PDF only** for any *new* web fetch (`%PDF` magic bytes). Never download/execute `.exe/.msi/.zip/.scr/.js`.
- **Deterministic rebuild:** extend `build_catalog_library.py` (or a Phase-2 sibling) so the manifest is regenerated with self-checks: local accounting balances, every `normalized_relpath` exists on disk, no binaries staged, row-count reported. Re-run `py_compile` + the builder before committing.
- **Canonical mfr vocab** follows the workbook `Manufacturers` sheet; `not_in_workbook=Y` when absent.

## Deliverable

Closeout handoff at `ops/agents/handoffs/2026-06-07-catalog-curation-phase2-closeout.md` reporting:
- final manifest row count + per-mfr / per-device-class distribution,
- the 12 reclassifications applied (with before/after relpath),
- long-tail rows added + every dedup decision (kept vs dropped, with reason + SHA where used),
- any `not_in_workbook=Y` vendors surfaced as **`tcc.mfr_aliases` candidates for CC review** (esp. Allis-Chalmers, the modern-licensed "Westinghouse" line),
- the commit hash(es).

CC will review the closeout, then promote any new mfr_aliases candidates and reconcile docs/memory. **Do not touch the live `tcc.*` tables or prod** — alias promotion is CC's governed lane.
