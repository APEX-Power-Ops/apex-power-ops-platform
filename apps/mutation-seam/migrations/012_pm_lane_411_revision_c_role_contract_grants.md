# PM Lane 411 Revision C - Role Contract Grants Migration Contract

Status: migration-equivalent contract only.

This file is intentionally documentation, not executable SQL. Current repo-local migrations `001` through `011` do not create the Lane 411 financial tables and do not apply the Revision A PM-and-Finance grant surface, so Revision C cannot truthfully claim to amend live SQL.

## Discovery Basis

1. No repo-local migration currently creates `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, or `seam.apparatus_revenue_events`.
2. No repo-local migration currently creates a `finance` or `operations` role for this Lane 411 surface.
3. The Lane 411 Revision A and Revision B financial-table grant model is design-only in this repo.
4. Revision C changes only the non-field role name from Finance to Operations while carrying the corrected four-table grant contract forward as first application.

## Future Application Contract

When a later admitted live packet creates the Lane 411 financial tables, the first truthful grant migration should do all of the following in the same admission surface:

1. Create the `operations` Postgres role if it does not already exist for this platform.
2. Grant schema usage needed for `pm` and `operations` on `seam`.
3. Grant SELECT and INSERT on `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, and `seam.apparatus_revenue_events` to `pm` and `operations`.
4. Preserve no SELECT or INSERT grant for `field_tech` and `field_lead` on the four financial tables.
5. Preserve any broader public-role deny posture already in use for `anon` and `authenticated`.

## Example Future SQL

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'operations') THEN
        CREATE ROLE operations NOLOGIN;
    END IF;
END;
$$;

GRANT USAGE ON SCHEMA seam TO pm, operations;

GRANT SELECT, INSERT ON TABLE seam.apparatus_financials TO pm, operations;
GRANT SELECT, INSERT ON TABLE seam.project_contract_snapshots TO pm, operations;
GRANT SELECT, INSERT ON TABLE seam.scope_labor_details TO pm, operations;
GRANT SELECT, INSERT ON TABLE seam.apparatus_revenue_events TO pm, operations;

REVOKE ALL ON TABLE seam.apparatus_financials FROM field_tech, field_lead;
REVOKE ALL ON TABLE seam.project_contract_snapshots FROM field_tech, field_lead;
REVOKE ALL ON TABLE seam.scope_labor_details FROM field_tech, field_lead;
REVOKE ALL ON TABLE seam.apparatus_revenue_events FROM field_tech, field_lead;
```

## Precision Note

This file is the first truthful forward contract for the corrected Lane 411 Revision C role surface. It does not imply that any prior Finance-role grant SQL was applied from this repo.

## Out Of Scope

This file does not admit live SQL execution, route implementation, hosted deployment, live business writes, `finance_authority` renaming, or any RESA Corporate accounting integration.