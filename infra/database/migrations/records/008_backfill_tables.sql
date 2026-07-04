-- =============================================================================
-- Records Domain — NETA Backfill tables (Chip 2-backfill)
-- Packet: 2026-06-16-records-2-backfill
-- Authority: reference/records/00-MASTER-INDEX.md §4 (the 2-level shell),
--            §5 (NETA seed). Requires: 005 (neta_procedures) + 007 (asset_classes).
--
-- Two links that scope each apparatus leaf's NETA universe and capture how NETA
-- procedures reference one another, so that:
--   * a leaf's applicable NETA = its linked procedures (the Chip-2b divergence is a
--     precise query at the leaf grain, not against the whole parent category);
--   * composite apparatus (MCC, harmonic filter) resolve their constituents through
--     the procedure->procedure graph + the asset tree, exactly as NETA models them.
-- =============================================================================

BEGIN;

-- Kind of inter-procedure reference.
CREATE TYPE records.neta_xref_kind_enum AS ENUM (
    'crossref',       -- a crossref-only procedure points to its constituents (MCC -> bus/switches/breakers/starters)
    'in_accordance'   -- a procedure borrows another's method ("in accordance with Section X"; LTC -> 7.2.2)
);

-- ---------------------------------------------------------------------------
-- records.asset_class_neta_procedure
--   Which NETA procedures apply to each apparatus LEAF class. Parents (NETA
--   categories) are not linked here -- they carry neta_category directly; assets
--   and templates attach at the leaf, so the applicable-procedure set lives there.
-- ---------------------------------------------------------------------------
CREATE TABLE records.asset_class_neta_procedure (
    asset_class_neta_procedure_id uuid NOT NULL DEFAULT gen_random_uuid(),
    asset_class_id    uuid    NOT NULL,
    neta_procedure_id uuid    NOT NULL,
    is_primary        boolean NOT NULL DEFAULT false,   -- the leaf's lead procedure (exactly one per leaf)
    created_at        timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT pk_asset_class_neta_procedure PRIMARY KEY (asset_class_neta_procedure_id),
    CONSTRAINT fk_acnp_class FOREIGN KEY (asset_class_id)
        REFERENCES records.asset_classes (asset_class_id) ON DELETE CASCADE,
    CONSTRAINT fk_acnp_procedure FOREIGN KEY (neta_procedure_id)
        REFERENCES records.neta_procedures (neta_procedure_id) ON DELETE CASCADE,
    CONSTRAINT uq_acnp UNIQUE (asset_class_id, neta_procedure_id)
);

COMMENT ON TABLE records.asset_class_neta_procedure IS
    'Which NETA procedures apply to each apparatus leaf class. Scopes the leaf''s '
    'NETA universe so the Chip-2b datasheet-vs-NETA divergence is a precise query.';

-- ---------------------------------------------------------------------------
-- records.neta_procedure_xref
--   The NETA procedure->procedure reference graph: composition (crossref) and
--   method borrowing (in_accordance). to_procedure_id resolves when the referenced
--   section is an exact procedure; category-level refs (7.1, 7.6) stay raw (NULL).
-- ---------------------------------------------------------------------------
CREATE TABLE records.neta_procedure_xref (
    neta_procedure_xref_id uuid NOT NULL DEFAULT gen_random_uuid(),
    from_procedure_id uuid    NOT NULL,
    to_section        text    NOT NULL,
    to_procedure_id   uuid    NULL,
    ref_kind          records.neta_xref_kind_enum NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT pk_neta_procedure_xref PRIMARY KEY (neta_procedure_xref_id),
    CONSTRAINT fk_npx_from FOREIGN KEY (from_procedure_id)
        REFERENCES records.neta_procedures (neta_procedure_id) ON DELETE CASCADE,
    CONSTRAINT fk_npx_to FOREIGN KEY (to_procedure_id)
        REFERENCES records.neta_procedures (neta_procedure_id) ON DELETE SET NULL,
    CONSTRAINT uq_npx UNIQUE (from_procedure_id, to_section, ref_kind)
);

COMMENT ON TABLE records.neta_procedure_xref IS
    'NETA procedure->procedure references: crossref composition (MCC -> its '
    'constituents) and in_accordance method borrowing (LTC -> 7.2.2). to_procedure_id '
    'resolves exact-section refs; category-level refs (7.1, 7.6) stay raw.';

CREATE INDEX ix_acnp_procedure ON records.asset_class_neta_procedure (neta_procedure_id);
CREATE INDEX ix_npx_from       ON records.neta_procedure_xref (from_procedure_id);
CREATE INDEX ix_npx_to         ON records.neta_procedure_xref (to_procedure_id);

COMMIT;
