# PM Lane 276 Render Completion Executor Closeout

1. Source commit tested

- Local source floor verified and Render deploy event confirmed: `c0f99ff89391334d674b0ea75a79ae85a89b3086` (`Add PM Lane 275 snapshot loader fallback`).

2. Existing Render service name

- `apex-platform-mutation-seam`
- Service ID: `srv-d7tg1657vvec738hstg0`

3. Authenticated surface used

- Authenticated Render dashboard in the internal browser.
- Used the existing service dashboard root and Environment pages.
- Did not expose or print secret values.

4. Selected path

- `snapshot env deploy`

5. Hosted runtime path used

- Snapshot runtime root resolved from `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH=/etc/secrets/candidate.json`
- Snapshot bundle runtime directory: `/etc/secrets`
- Existing Render Secret Files surface provided the runtime-accessible hosted path.

6. File placement evidence without payload contents

- Local snapshot hashes verified before transfer:
  - `candidate.json` -> `813013d12cab476ffa67cfbb42d0421bc107d5e189a229e2450f490fc9022445`
  - `admission-plan.json` -> `b370e6999e9beddc5ae70feca8454052c001dec47dc42fcfc19269d853ce01cd`
  - `manifest.json` -> `80a05dcc70728099ee52ff0f80204feee5e6f4102334f919837016ef89b87f95`
- Render Environment -> Secret Files showed the mounted filenames after save:
  - `.env`
  - `admission-plan.json`
  - `candidate.json`
  - `manifest.json`
  - `SHA256SUMS.txt`
- No snapshot payload contents were printed during placement or closeout.

7. Env var key presence and non-secret path summary

- Existing key presence confirmed on the Environment page without printing values:
  - `SEAM_DATABASE_URL`
  - `JWT_SECRET`
- The snapshot path was supplied through the mounted `.env` secret file so the running app loads:
  - `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH=/etc/secrets/candidate.json`
- Hosted application behavior proved the setting was effective after redeploy.

8. Storage and transfer method used

- No persistent disk was attached to the service at execution time; Render Disk page showed only `Add Disk`.
- Used the existing Render Secret Files runtime path on the existing service.
- No SSH/SCP used.
- No dashboard shell used.
- No new paid disk, bucket, service, database, or external file authority created.

9. Restart/redeploy evidence

- Render service root page recorded:
  - `Deploy started for c0f99ff: Add PM Lane 275 snapshot loader fallback`
  - `Environment updated`
  - `May 17, 2026 at 6:43 PM`
  - `Deploy live for c0f99ff: Add PM Lane 275 snapshot loader fallback`
  - `May 17, 2026 at 6:43 PM`

10. Exact validation command outputs

- `& ".venv/Scripts/python.exe" "apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake`

```text
health status=200 detail=ok
root status=200 detail=ok
reads_approval_queue status=200 detail=ok
schedule_projects status=200 detail=ok
schedule_drivers status=200 detail=ok
schedule_tracer status=200 detail=ok
schedule_variance status=200 detail=ok
openapi status=200 detail=ok
project_import_candidate status=200 detail=ok
project_import_admission_plan status=200 detail=ok
project_import_approval_contract status=200 detail=ok
project_import_approval_storage_plan status=200 detail=ok
project_import_approval_status status=200 detail=ok
RESULT PASS
```

- `corepack pnpm --dir "." --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000`

```text
PM_INTAKE_HOSTED_OK operations-web import candidate
PM_INTAKE_HOSTED_OK operations-web import admission plan
PM_INTAKE_HOSTED_OK operations-web import approval readiness
PM_INTAKE_HOSTED_OK operations-web import intake workbench
PM_INTAKE_HOSTED_OK mutation seam health
PM_INTAKE_HOSTED_OK mutation seam OpenAPI intake and approval paths
PM_INTAKE_HOSTED_OK mutation seam import candidate read
PM_INTAKE_HOSTED_OK mutation seam import admission plan read
PM_INTAKE_HOSTED_OK mutation seam import approval contract read
PM_INTAKE_HOSTED_OK mutation seam import approval storage plan read
PM_INTAKE_HOSTED_OK mutation seam import approval status read
PM_INTAKE_HOSTED_SUMMARY failed=0 operations_web_base_url=https://operations.apexpowerops.com/ mutation_seam_base_url=https://mutation-seam.apexpowerops.com/
```

- Exact Temp Power readback command returned:

```json
{"apparatus_candidates": 184, "approval_status_classification": "no_approval_record", "candidate_id": "pm-import-candidate-miner-temp-power", "candidate_shape_fingerprint": "ddc49565eb586af913ad48b2", "mutation_authority": "not_admitted", "source_stat_fingerprint": "e111fdbe934bf9de07ed24c1", "tasks": 15, "warning_code": "PROJECT_DATA_ENTRY_FORMULA_ERRORS", "workpackages": 7}
```

- Minimal MCP trio status command returned:

```json
{"status":"not-running"}
```

11. Hosted candidate readback summary

- Hosted `GET /api/v1/reads/project-import-candidate` now returns `pm-import-candidate-miner-temp-power`.
- Hosted counts match the packet target: `7` workpackages, `15` tasks, `184` apparatus candidates.
- Hosted source freshness fingerprint: `e111fdbe934bf9de07ed24c1`.
- Hosted admission-plan shape fingerprint: `ddc49565eb586af913ad48b2`.
- Hosted mutation/import authority remains `not_admitted`.
- Hosted approval status classification remains `no_approval_record`.

12. Final outcome label

- `RENDER_SNAPSHOT_ENV_DEPLOY_PASS_NO_APPROVAL_POST`

13. Guardrail confirmation

- No `POST /api/v1/mutations/project-import-approvals` request sent.
- No approval row created.
- No project import mutation sent.
- No SQL writes or schema migrations executed.
- No new Render service, disk, bucket, database, DNS, auth, ingress, or topology change created.
- No secrets printed, rotated, or modified.
- No source workbook or PDF contents were opened, uploaded, or mutated.
- No PM business-state mutation performed beyond hosted read-only validation and existing-service configuration needed for the snapshot runtime path.