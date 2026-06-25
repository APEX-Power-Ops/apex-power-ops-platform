/**
 * Hosted integration smoke — estimator native intake pipeline.
 *
 * Proves the LIVE server + DB + metadata path for the native estimator
 * intake without importing the source-only TS @apex/estimator-core
 * package (node v20 cannot strip types without --experimental-strip-types).
 * Instead, the envelope is hand-constructed to match the shape that
 * native.py::validate_envelope and pivot_to_intake_payload accept.  The
 * economic reconciliation is explicit and documented inline.
 *
 * DEVIATION from plan Task 7: `buildNativeEnvelope` from @apex/estimator-core
 * is NOT imported here.  The host's node v20.20.2 cannot run the source-only
 * TypeScript package at runtime.  The envelope-build layer is already proven
 * by Task 4 vitest + cross-contract field check.  This smoke's job is the
 * LIVE server+DB+metadata path, which does not require the TS import.
 *
 * Envelope economics (verified by hand — bid_cents = adjusted_cents):
 *   model: "Capcitors - Per Unit"  ref_hours.ATS = 1.0
 *   qty   = 1, m4 = 1, n4 = 1
 *   onsite_labor_cents = 500  (arbitrary positive integer)
 *   offsite_labor_cents = 0, cost_cents = 0, service_cents = 0
 *   adjusted_cents = onsite_labor_cents * m4 * n4 = 500
 *   bid_cents = adjusted_cents = 500
 *   resolved_ref_hours = 1.0 (matches catalog ATS ref_hours)
 *   quoted_app_hours = qty * resolved_ref_hours = 1 * 1.0 = 1.0
 *
 * Pipeline (when run live at the finish gate):
 *   1. POST /api/v1/ops/intake/native  {uploaded_by, envelope}
 *      → assert status === "parsed"
 *   2. POST /api/v1/ops/intake/{run_id}/approve  {approved_by}
 *      → assert status === "approved"
 *   3. GET  /api/v1/ops/recognition/worklist?project_number=<PROJECT>
 *      → assert rows.length > 0
 */

// ---------------------------------------------------------------------------
// Unique per-run disposable project guard
// ---------------------------------------------------------------------------
const PROJECT =
  process.env.SMOKE_PROJECT ||
  `DEMO-RENDERER-SMOKE-${new Date().toISOString().replace(/[^0-9]/g, '').slice(0, 14)}`;

if (PROJECT === 'DEMO-NATIVE-001' || PROJECT.startsWith('MINER')) {
  throw new Error(
    `smoke-estimator-native: refusing reserved/Miner project name: ${PROJECT}`,
  );
}

// ---------------------------------------------------------------------------
// Configuration from environment
// ---------------------------------------------------------------------------
const BASE_URL = (
  process.env.CONTROL_PLANE_BASE_URL || 'http://127.0.0.1:8010'
).replace(/\/$/, '');

/**
 * Actor UUID — the dev PM actor seeded in ops_dev.
 * Must be a row in ops.persons.
 */
const ACTOR =
  process.env.PM_ID || '0a000000-0000-4000-8000-000000000001';

const TIMEOUT_MS = Number(
  process.env.SMOKE_TIMEOUT_MS || '20000',
);

if (!Number.isFinite(TIMEOUT_MS) || TIMEOUT_MS <= 0) {
  throw new Error(`smoke-estimator-native: invalid SMOKE_TIMEOUT_MS=${TIMEOUT_MS}`);
}

// ---------------------------------------------------------------------------
// Hand-constructed server-shaped native envelope
//
// Shape contract: native.py::validate_envelope + pivot_to_intake_payload.
// See packages/ops-intake/tests/test_native_envelope.py::_catalog_env for the
// canonical fixture this mirrors.
//
// Economics reconciliation (all assertions at runtime in reconcileEnvelope):
//   bid_cents   = 500
//   scope onsite_labor_cents = 500, offsite=0, cost=0, service=0
//   adjusted_cents = onsite * m4(1) * n4(1) = 500  ✓ bid_cents === adjusted_cents
//   base_qty === project_intake_qty (required at M4=1) = 1
//   resolved_ref_hours = 1.0 (Capcitors - Per Unit ATS ref_hours in the seed catalog)
// ---------------------------------------------------------------------------
function buildEnvelope(projectNumber) {
  const BID_CENTS = 500;
  const ONSITE_LABOR_CENTS = 500; // all labor is onsite; offsite = 0
  const QTY = 1;
  const RESOLVED_REF_HOURS = 1.0; // ATS ref_hours for "Capcitors - Per Unit" (seed catalog)
  const QUOTED_APP_HOURS = QTY * RESOLVED_REF_HOURS; // = 1.0

  return {
    schema_version: 'estimate_envelope_v1',
    source_kind: 'native',
    project_number: projectNumber,
    envelope_id: `env-smoke-${Date.now()}`,
    quote_version: 1,
    content_hash: 'smoke-placeholder', // server recomputes C6
    source_draft_id: 'smoke-draft-1',
    source_revision_id: 'smoke-rev-1',
    totals: {
      bid_cents: BID_CENTS,
      service_hours: 0,
    },
    scopes: [
      {
        scope_id: 'SC1',
        name: 'ATS Scope',
        neta_standard: 'ATS',
        replication_m4: 1,
        adjustment_multiplier_n4: 1,
        scope_totals: {
          onsite_labor_cents: ONSITE_LABOR_CENTS,
          offsite_labor_cents: 0,
          cost_cents: 0,         // validate_envelope rejects nonzero_cost
          service_cents: 0,       // validate_envelope rejects nonzero_service
          quoted_app_hours: QUOTED_APP_HOURS,
          adjusted_cents: BID_CENTS, // onsite * m4 * n4 = 500 * 1 * 1 = 500 ✓
        },
        lines: [
          {
            line_uid: 'SC1:cap-1',
            line_kind: 'catalog',
            included: true,
            equipment_model_ref: 'Capcitors - Per Unit',
            base_qty: QTY,
            project_intake_qty: QTY, // must equal base_qty when m4=1
            resolved_ref_hours: RESOLVED_REF_HOURS,
            // Three metadata fields required by Task 4/7 and load.py
            designation: 'CAP-ATS-1',
            notes: 'Smoke test capacitor unit',
            description: 'Capcitors per unit — estimator native smoke',
          },
        ],
      },
    ],
  };
}

/**
 * Static reconciliation check: confirm the envelope we hand-built satisfies
 * the economic invariants before sending it over the wire.
 */
function reconcileEnvelope(env) {
  const scope = env.scopes[0];
  const line = scope.lines[0];
  const tot = scope.scope_totals;

  const expectedAdjusted = tot.onsite_labor_cents * scope.replication_m4 * scope.adjustment_multiplier_n4;
  if (Math.abs(tot.adjusted_cents - expectedAdjusted) > 1) {
    throw new Error(
      `smoke-estimator-native: envelope economics broken: ` +
      `adjusted_cents=${tot.adjusted_cents} expected=${expectedAdjusted}`,
    );
  }
  if (Math.abs(env.totals.bid_cents - tot.adjusted_cents) > 1) {
    throw new Error(
      `smoke-estimator-native: bid_cents (${env.totals.bid_cents}) !== adjusted_cents (${tot.adjusted_cents})`,
    );
  }
  if (line.base_qty !== line.project_intake_qty) {
    throw new Error(
      `smoke-estimator-native: base_qty (${line.base_qty}) !== project_intake_qty (${line.project_intake_qty}) — required when m4=1`,
    );
  }
  if (line.line_kind !== 'catalog') {
    throw new Error(`smoke-estimator-native: line_kind must be 'catalog'`);
  }
  if (!line.designation || !line.notes || !line.description) {
    throw new Error(
      `smoke-estimator-native: envelope line is missing designation/notes/description`,
    );
  }
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------
async function fetchJson(url, options) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response;
  try {
    response = await fetch(url, { ...options, signal: controller.signal });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`HTTP fetch failed for ${url}: ${msg}`);
  } finally {
    clearTimeout(timeout);
  }
  const text = await response.text();
  if (!response.ok) {
    throw new Error(
      `HTTP ${response.status} from ${url}${text ? ` — ${text.slice(0, 300)}` : ''}`,
    );
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Non-JSON response from ${url}: ${text.slice(0, 200)}`);
  }
}

async function postJson(path, body) {
  return fetchJson(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

async function getJson(path) {
  return fetchJson(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
}

// ---------------------------------------------------------------------------
// Assertion runner (mirrors smoke-pm-intake-hosted.mjs style)
// ---------------------------------------------------------------------------
async function runStep(label, failures, fn) {
  try {
    await fn();
    console.log(`ESTIMATOR_NATIVE_SMOKE_OK ${label}`);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`ESTIMATOR_NATIVE_SMOKE_FAIL ${label} — ${msg}`);
    failures.push(`${label}: ${msg}`);
  }
}

// ---------------------------------------------------------------------------
// Main pipeline
// ---------------------------------------------------------------------------
async function main() {
  const failures = [];
  let runId = null;

  // Step 0: Verify the envelope is economically sound before sending anything
  await runStep('envelope-economics-reconcile', failures, () => {
    const env = buildEnvelope(PROJECT);
    reconcileEnvelope(env);
  });

  // Step 1: POST /api/v1/ops/intake/native
  await runStep('POST /native → status===parsed', failures, async () => {
    const envelope = buildEnvelope(PROJECT);
    reconcileEnvelope(envelope); // double-check before wire
    const result = await postJson('/api/v1/ops/intake/native', {
      uploaded_by: ACTOR,
      envelope,
    });
    if (result.status !== 'parsed') {
      const findingsText = Array.isArray(result.findings)
        ? result.findings.map((f) => `[${f.code}] ${f.message}`).join('; ')
        : JSON.stringify(result.findings);
      throw new Error(
        `expected status "parsed" got "${result.status}"${findingsText ? ` — findings: ${findingsText}` : ''}`,
      );
    }
    if (!result.run_id) {
      throw new Error('response missing run_id');
    }
    runId = result.run_id;
    console.log(`  run_id=${runId} source_format=${result.source_format}`);
  });

  // Step 2: POST /api/v1/ops/intake/{run_id}/approve
  // NOTE: This step will succeed only when migration 011 has been applied to
  // ops_dev (adds the description column load.py now INSERTs).  The live run
  // is DEFERRED to the operator finish gate.  The smoke exits before this step
  // if step 1 failed (no run_id).
  await runStep('POST /{run_id}/approve → status===approved', failures, async () => {
    if (!runId) {
      throw new Error('skipped — no run_id (step 1 failed)');
    }
    const result = await postJson(`/api/v1/ops/intake/${runId}/approve`, {
      approved_by: ACTOR,
    });
    if (result.status !== 'approved') {
      throw new Error(
        `expected status "approved" got "${result.status || JSON.stringify(result)}"`,
      );
    }
  });

  // Step 3: GET /api/v1/ops/recognition/worklist?project_number=<PROJECT>
  await runStep(
    `GET /recognition/worklist?project_number=${PROJECT} → rows > 0`,
    failures,
    async () => {
      if (!runId) {
        throw new Error('skipped — no run_id (step 1 failed)');
      }
      const rows = await getJson(
        `/api/v1/ops/recognition/worklist?project_number=${encodeURIComponent(PROJECT)}`,
      );
      if (!Array.isArray(rows) || rows.length === 0) {
        throw new Error(
          `expected at least one worklist row for project ${PROJECT}, got ${JSON.stringify(rows).slice(0, 200)}`,
        );
      }
      console.log(`  worklist rows=${rows.length} for project_number=${PROJECT}`);
    },
  );

  // Step 4: DB persistence — assert metadata actually landed in ops.scope_quote_line
  // Fails closed when OPS_DEV_DSN is unset, unless ALLOW_DB_CHECK_SKIP=1 (API-only runs).
  await runStep(
    `DB ops.scope_quote_line metadata persisted for line_uid='SC1:cap-1'`,
    failures,
    async () => {
      const dsn = process.env.OPS_DEV_DSN;
      if (!dsn) {
        if (process.env.ALLOW_DB_CHECK_SKIP === '1') {
          console.warn(
            '  ESTIMATOR_NATIVE_SMOKE_WARN OPS_DEV_DSN unset — DB persistence check skipped (ALLOW_DB_CHECK_SKIP=1)',
          );
          return;
        }
        throw new Error(
          'OPS_DEV_DSN is unset — DB persistence check cannot run. ' +
          'Set ALLOW_DB_CHECK_SKIP=1 to intentionally skip (API-only run).',
        );
      }
      if (!runId) {
        throw new Error('skipped — no run_id (step 1 failed)');
      }

      // Import child_process without a top-level import so the file parses even in
      // environments that do not use this code path.
      const { execFileSync } = await import('child_process');

      // Parse the libpq DSN ("key=value ..." whitespace-separated) into PG* env vars
      // so the password never appears in psql argv (visible in ps output).
      const dsnKeyMap = { host: 'PGHOST', port: 'PGPORT', dbname: 'PGDATABASE', user: 'PGUSER', password: 'PGPASSWORD', sslmode: 'PGSSLMODE' };
      const pgEnv = { ...process.env };
      for (const token of dsn.trim().split(/\s+/)) {
        const eqIdx = token.indexOf('=');
        if (eqIdx < 1) continue;
        const key = token.slice(0, eqIdx);
        const val = token.slice(eqIdx + 1);
        if (Object.prototype.hasOwnProperty.call(dsnKeyMap, key)) {
          pgEnv[dsnKeyMap[key]] = val;
        }
      }

      // Query: join through scopes→projects to scope to our disposable project.
      // Use $1 placeholder to pass PROJECT; pass literal string for line_uid
      // (controlled constant — not user input).
      const sql =
        `select ql.designation, ql.notes, ql.description` +
        ` from ops.scope_quote_line ql` +
        ` join ops.scopes s   on s.id = ql.scope_id` +
        ` join ops.projects p on p.id = s.project_id` +
        ` where p.project_number = '${PROJECT.replace(/'/g, "''")}'` +
        `   and ql.legacy_source_id = 'SC1:cap-1'`;

      // Run psql with PG* env vars — no connection string in argv.
      let stdout;
      try {
        stdout = execFileSync(
          'psql',
          ['-t', '-A', '-F|', '-c', sql],
          { encoding: 'utf8', timeout: 10000, env: pgEnv },
        ).trim();
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        throw new Error(`psql query failed: ${msg}`);
      }

      if (!stdout) {
        throw new Error(
          `DB persistence check: no row found in ops.scope_quote_line for ` +
          `project_number='${PROJECT}' and legacy_source_id='SC1:cap-1'`,
        );
      }

      // Expected values — must exactly match the envelope submitted in Step 1.
      const EXPECTED_DESIGNATION  = 'CAP-ATS-1';
      const EXPECTED_NOTES        = 'Smoke test capacitor unit';
      const EXPECTED_DESCRIPTION  = 'Capcitors per unit — estimator native smoke';

      const parts = stdout.split('|');
      if (parts.length !== 3) {
        throw new Error(
          `DB persistence check: unexpected row format (expected 3 pipe-separated fields): ${stdout.slice(0, 200)}`,
        );
      }
      const [actualDesignation, actualNotes, actualDescription] = parts;

      const mismatches = [];
      if (actualDesignation !== EXPECTED_DESIGNATION) {
        mismatches.push(`designation: expected="${EXPECTED_DESIGNATION}" actual="${actualDesignation}"`);
      }
      if (actualNotes !== EXPECTED_NOTES) {
        mismatches.push(`notes: expected="${EXPECTED_NOTES}" actual="${actualNotes}"`);
      }
      if (actualDescription !== EXPECTED_DESCRIPTION) {
        mismatches.push(`description: expected="${EXPECTED_DESCRIPTION}" actual="${actualDescription}"`);
      }
      if (mismatches.length > 0) {
        throw new Error(
          `DB persistence mismatch — ${mismatches.join('; ')}`,
        );
      }

      console.log(
        `  DB row confirmed: designation="${actualDesignation}" notes="${actualNotes}" description="${actualDescription}"`,
      );
    },
  );

  // Summary
  if (failures.length > 0) {
    console.error(
      `ESTIMATOR_NATIVE_SMOKE_SUMMARY FAIL failed=${failures.length} project=${PROJECT} base_url=${BASE_URL}`,
    );
    process.exitCode = 1;
    return;
  }

  console.log(
    `ESTIMATOR_NATIVE_SMOKE_SUMMARY PASS failed=0 project=${PROJECT} base_url=${BASE_URL}`,
  );
}

main().catch((err) => {
  const msg = err instanceof Error ? err.message : String(err);
  console.error(`ESTIMATOR_NATIVE_SMOKE_FATAL ${msg}`);
  process.exitCode = 1;
});
