-- =============================================================================
-- Org Domain -- Core Tables
-- Packet: 2026-04-14-pm-schema-011b
-- Authority: 2026-04-14-pm-schema-011a-org-domain-schema-design-handoff.md §2
-- Landing Lane: infra/database/migrations/org/
--
-- Dependency order:
--   clients -> sites -> (standalone: business_units) -> contracts
--
-- These four tables are the minimum org-domain surface required to support
-- later activation of the six deferred PM/work foreign keys:
--   work.projects.client_id        -> org.clients
--   work.projects.site_id          -> org.sites
--   work.projects.business_unit_id -> org.business_units
--   work.projects.contract_id      -> org.contracts
--   work.work_packages.client_id   -> org.clients
--   work.work_packages.site_id     -> org.sites
--
-- This file does NOT activate those PM/work foreign keys. FK activation
-- is deferred to packet 011d after seed-data population (011c).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- org.clients
-- ---------------------------------------------------------------------------

CREATE TABLE org.clients (
    client_id           uuid            NOT NULL DEFAULT gen_random_uuid(),
    client_code         text            NOT NULL,
    name                text            NOT NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_clients PRIMARY KEY (client_id),
    CONSTRAINT uq_clients_client_code UNIQUE (client_code)
);

COMMENT ON TABLE org.clients IS
    'Customer entity. Every PM/work project and work package references a client. '
    'Packet 011a §2.2.';

-- ---------------------------------------------------------------------------
-- org.sites
-- ---------------------------------------------------------------------------

CREATE TABLE org.sites (
    site_id             uuid            NOT NULL DEFAULT gen_random_uuid(),
    client_id           uuid            NOT NULL,
    site_code           text            NOT NULL,
    name                text            NOT NULL,
    address_line_1      text            NULL,
    city                text            NULL,
    state_province      text            NULL,
    postal_code         text            NULL,
    country             text            NULL DEFAULT 'US',
    is_active           boolean         NOT NULL DEFAULT true,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_sites PRIMARY KEY (site_id),
    CONSTRAINT fk_sites_client
        FOREIGN KEY (client_id) REFERENCES org.clients (client_id),
    CONSTRAINT uq_sites_client_code UNIQUE (client_id, site_code)
);

COMMENT ON TABLE org.sites IS
    'Physical location where work is performed. Sites belong to a client. '
    'Packet 011a §2.3.';

-- ---------------------------------------------------------------------------
-- org.business_units
-- ---------------------------------------------------------------------------

CREATE TABLE org.business_units (
    business_unit_id    uuid            NOT NULL DEFAULT gen_random_uuid(),
    code                text            NOT NULL,
    name                text            NOT NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_business_units PRIMARY KEY (business_unit_id),
    CONSTRAINT uq_business_units_code UNIQUE (code)
);

COMMENT ON TABLE org.business_units IS
    'Internal organizational grouping (e.g. Electrical Testing, Commissioning). '
    'Standalone -- no parent FK within org. Packet 011a §2.4.';

-- ---------------------------------------------------------------------------
-- org.contracts
-- ---------------------------------------------------------------------------

CREATE TABLE org.contracts (
    contract_id         uuid            NOT NULL DEFAULT gen_random_uuid(),
    client_id           uuid            NOT NULL,
    contract_code       text            NOT NULL,
    title               text            NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_contracts PRIMARY KEY (contract_id),
    CONSTRAINT fk_contracts_client
        FOREIGN KEY (client_id) REFERENCES org.clients (client_id),
    CONSTRAINT uq_contracts_contract_code UNIQUE (contract_code)
);

COMMENT ON TABLE org.contracts IS
    'Commercial agreement under which work is performed. Contracts belong to a client. '
    'Optional on PM/work projects (contract_id is nullable). Packet 011a §2.5.';
