-- =============================================================================
-- 007_work_org_fk_activation.sql
-- PM Schema Packet 011d — Activate 6 Deferred Org Foreign Keys
-- =============================================================================
-- Activates the six cross-schema FK constraints from work.projects and
-- work.work_packages into the org schema tables created by packet 011b
-- and populated by packet 011c.
--
-- Prerequisites:
--   - org schema exists with 4 tables (clients, sites, business_units, contracts)
--   - seed data covers all non-NULL client_id/site_id values in work tables
--   - all 4 coverage verification queries return zero orphaned rows
--
-- Constraints activated (6 total):
--   work.projects     → org.clients        (client_id, NOT NULL)
--   work.projects     → org.sites          (site_id, NOT NULL)
--   work.projects     → org.business_units (business_unit_id, nullable)
--   work.projects     → org.contracts      (contract_id, nullable)
--   work.work_packages → org.clients       (client_id, NOT NULL)
--   work.work_packages → org.sites         (site_id, NOT NULL)
-- =============================================================================

-- ---------- work.projects → org.clients ----------
ALTER TABLE work.projects
  ADD CONSTRAINT fk_projects_client
  FOREIGN KEY (client_id) REFERENCES org.clients (client_id);

-- ---------- work.projects → org.sites ----------
ALTER TABLE work.projects
  ADD CONSTRAINT fk_projects_site
  FOREIGN KEY (site_id) REFERENCES org.sites (site_id);

-- ---------- work.projects → org.business_units ----------
ALTER TABLE work.projects
  ADD CONSTRAINT fk_projects_business_unit
  FOREIGN KEY (business_unit_id) REFERENCES org.business_units (business_unit_id);

-- ---------- work.projects → org.contracts ----------
ALTER TABLE work.projects
  ADD CONSTRAINT fk_projects_contract
  FOREIGN KEY (contract_id) REFERENCES org.contracts (contract_id);

-- ---------- work.work_packages → org.clients ----------
ALTER TABLE work.work_packages
  ADD CONSTRAINT fk_work_packages_client
  FOREIGN KEY (client_id) REFERENCES org.clients (client_id);

-- ---------- work.work_packages → org.sites ----------
ALTER TABLE work.work_packages
  ADD CONSTRAINT fk_work_packages_site
  FOREIGN KEY (site_id) REFERENCES org.sites (site_id);
