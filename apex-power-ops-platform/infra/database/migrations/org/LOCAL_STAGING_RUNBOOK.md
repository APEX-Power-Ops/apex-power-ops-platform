# Org Domain Local Staging Runbook
## Packet: 2026-04-14-pm-schema-011b
## Target: Local PostgreSQL staging database `apex_pm_stage`

## Prerequisites

- The `apex_pm_stage` database must already exist with the `work` schema from packet 007/008
- The `org` schema must NOT already exist (or must be dropped first)

## Validation Stages

### Stage 1 -- Structural Fidelity

After executing all 3 SQL files in order, verify:

```sql
-- 1a. Schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'org';
-- Expected: 1 row

-- 1b. Table count
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'org' AND table_type = 'BASE TABLE';
-- Expected: 4

-- 1c. Table names
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'org' AND table_type = 'BASE TABLE'
ORDER BY table_name;
-- Expected: business_units, clients, contracts, sites

-- 1d. Trigger function exists
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'org' AND routine_name = 'fn_set_updated_at';
-- Expected: 1 row

-- 1e. Trigger count
SELECT COUNT(*) FROM information_schema.triggers
WHERE trigger_schema = 'org';
-- Expected: 4
```

### Stage 2 -- Constraint Integrity

```sql
-- 2a. Internal FK: sites.client_id -> clients
INSERT INTO org.clients (client_code, name) VALUES ('TEST-001', 'Test Client');
INSERT INTO org.sites (client_id, site_code, name)
    VALUES ((SELECT client_id FROM org.clients WHERE client_code = 'TEST-001'), 'SITE-001', 'Test Site');
-- Expected: both succeed

-- 2b. FK violation: site with nonexistent client
INSERT INTO org.sites (client_id, site_code, name)
    VALUES (gen_random_uuid(), 'SITE-BAD', 'Bad Site');
-- Expected: FK violation error

-- 2c. Internal FK: contracts.client_id -> clients
INSERT INTO org.contracts (client_id, contract_code)
    VALUES ((SELECT client_id FROM org.clients WHERE client_code = 'TEST-001'), 'CTR-001');
-- Expected: succeeds

-- 2d. FK violation: contract with nonexistent client
INSERT INTO org.contracts (client_id, contract_code)
    VALUES (gen_random_uuid(), 'CTR-BAD');
-- Expected: FK violation error

-- 2e. UNIQUE violation: duplicate client_code
INSERT INTO org.clients (client_code, name) VALUES ('TEST-001', 'Duplicate');
-- Expected: unique violation error

-- 2f. UNIQUE violation: duplicate site_code within same client
INSERT INTO org.sites (client_id, site_code, name)
    VALUES ((SELECT client_id FROM org.clients WHERE client_code = 'TEST-001'), 'SITE-001', 'Dup Site');
-- Expected: unique violation error

-- 2g. UNIQUE cross-client: same site_code under different client is allowed
INSERT INTO org.clients (client_code, name) VALUES ('TEST-002', 'Second Client');
INSERT INTO org.sites (client_id, site_code, name)
    VALUES ((SELECT client_id FROM org.clients WHERE client_code = 'TEST-002'), 'SITE-001', 'Same Code Different Client');
-- Expected: succeeds (site_code UNIQUE is scoped to client_id)

-- 2h. Business unit standalone
INSERT INTO org.business_units (code, name) VALUES ('ET', 'Electrical Testing');
-- Expected: succeeds

-- 2i. UNIQUE violation: duplicate business_unit code
INSERT INTO org.business_units (code, name) VALUES ('ET', 'Duplicate');
-- Expected: unique violation error
```

### Stage 3 -- Contract Compliance (updated_at trigger)

```sql
-- 3a. Verify updated_at auto-maintenance on clients
UPDATE org.clients SET name = 'Updated Name' WHERE client_code = 'TEST-001';
SELECT client_code, (updated_at > created_at) AS updated_at_advanced
FROM org.clients WHERE client_code = 'TEST-001';
-- Expected: updated_at_advanced = true

-- 3b. Verify updated_at on sites
UPDATE org.sites SET name = 'Updated Site' WHERE site_code = 'SITE-001'
    AND client_id = (SELECT client_id FROM org.clients WHERE client_code = 'TEST-001');
SELECT site_code, (updated_at > created_at) AS updated_at_advanced
FROM org.sites WHERE site_code = 'SITE-001'
    AND client_id = (SELECT client_id FROM org.clients WHERE client_code = 'TEST-001');
-- Expected: updated_at_advanced = true

-- 3c. Verify updated_at on business_units
UPDATE org.business_units SET name = 'Updated BU' WHERE code = 'ET';
SELECT code, (updated_at > created_at) AS updated_at_advanced
FROM org.business_units WHERE code = 'ET';
-- Expected: updated_at_advanced = true

-- 3d. Verify updated_at on contracts
UPDATE org.contracts SET title = 'Updated Contract'
    WHERE contract_code = 'CTR-001';
SELECT contract_code, (updated_at > created_at) AS updated_at_advanced
FROM org.contracts WHERE contract_code = 'CTR-001';
-- Expected: updated_at_advanced = true
```

### Stage 4 -- Cross-Domain Isolation

```sql
-- 4a. Confirm work schema is untouched
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'work' AND table_type = 'BASE TABLE'
ORDER BY table_name;
-- Expected: 8 tables (assignments, dependencies, execution_issues, progress_snapshots,
--           projects, tasks, wbs_nodes, work_packages)

-- 4b. Confirm no new FKs on work tables referencing org
SELECT tc.constraint_name, tc.table_schema, tc.table_name,
       ccu.table_schema AS foreign_schema, ccu.table_name AS foreign_table
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'work'
    AND ccu.table_schema = 'org';
-- Expected: 0 rows (no work->org FKs activated)
```

## Cleanup After Validation

```sql
-- Remove test data (if running validation in staging)
DELETE FROM org.sites;
DELETE FROM org.contracts;
DELETE FROM org.business_units;
DELETE FROM org.clients;
```
