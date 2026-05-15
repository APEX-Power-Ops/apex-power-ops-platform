import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(HERE, '..');
const DEFAULT_OPERATIONS_WEB_BASE_URL = 'http://127.0.0.1:3000';
const DEFAULT_MUTATION_SEAM_BASE_URL = 'http://127.0.0.1:8000';

function parseArgs(argv) {
  const parsed = {};

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];

    if (argument === '--') {
      continue;
    }

    if (argument === '--help' || argument === '-h') {
      parsed.help = true;
      continue;
    }

    if (!argument.startsWith('--')) {
      throw new Error(`Unknown argument: ${argument}`);
    }

    const key = argument.slice(2);
    const value = argv[index + 1];

    if (!value || value.startsWith('--')) {
      throw new Error(`Missing value for --${key}`);
    }

    parsed[key] = value;
    index += 1;
  }

  return parsed;
}

function printUsage() {
  console.log(
    'Usage: node scripts/smoke-pm-live-data.mjs [--operations-web-base-url <url>] [--mutation-seam-base-url <url>] [--timeout-ms <ms>]'
  );
}

function normalizeBaseUrl(rawBaseUrl) {
  const url = new URL(rawBaseUrl);
  url.pathname = url.pathname.endsWith('/') ? url.pathname : `${url.pathname}/`;
  return url;
}

async function expectJson(url, label, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      headers: {
        accept: 'application/json',
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`${label} returned HTTP ${response.status}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

async function expectHtml(url, label, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      headers: {
        accept: 'text/html,application/xhtml+xml',
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`${label} returned HTTP ${response.status}`);
    }

    const contentType = response.headers.get('content-type') ?? '';

    if (!contentType.includes('text/html')) {
      throw new Error(`${label} returned unexpected content-type ${contentType || '<empty>'}`);
    }
  } finally {
    clearTimeout(timeout);
  }
}

function collectWorkfrontEntityIds(workfront, maxIds = 5) {
  const ids = new Set();

  for (const row of workfront.rows ?? []) {
    if (row.primary_blocking_issue_id) {
      ids.add(String(row.primary_blocking_issue_id));
    }
    if (row.returnable_issue_id) {
      ids.add(String(row.returnable_issue_id));
    }
    if (row.last_pm_decision?.entity_id) {
      ids.add(String(row.last_pm_decision.entity_id));
    }
    for (const issue of row.blocking_issues ?? []) {
      if (issue.id) {
        ids.add(String(issue.id));
      }
    }
  }

  return Array.from(ids).slice(0, maxIds);
}

function assertPmWorkfront(workfront) {
  if (!workfront || typeof workfront !== 'object') {
    throw new Error('PM workfront returned a non-object payload');
  }

  const totalCount = Number(workfront.summary?.total_count ?? workfront.rows?.length ?? 0);
  if (!Number.isFinite(totalCount) || totalCount < 0) {
    throw new Error(`PM workfront returned an invalid total_count: ${workfront.summary?.total_count}`);
  }

  if (!Array.isArray(workfront.rows)) {
    throw new Error('PM workfront returned rows that are not an array');
  }

  const aiAuthority = workfront.advisory?.ai_mutation_authority;
  const advisoryMode = workfront.advisory?.mode;
  if (advisoryMode && advisoryMode !== 'read_only') {
    throw new Error(`PM workfront returned unexpected advisory mode: ${advisoryMode}`);
  }
  if (aiAuthority && aiAuthority !== 'not_admitted') {
    throw new Error(`PM workfront returned unexpected AI mutation authority: ${aiAuthority}`);
  }
}

function decisionHistoryUrl(baseUrl, entityIds, limit = 25) {
  const url = new URL('api/v1/reads/decision-history', baseUrl);
  const scopedEntityIds = entityIds.length ? entityIds : ['__pm_workfront_smoke_noop__'];
  for (const entityId of scopedEntityIds) {
    url.searchParams.append('entity_id', entityId);
  }
  url.searchParams.set('limit', String(limit));
  return url;
}

function assertDecisionHistory(history, entityIds, limit = 25) {
  if (!Array.isArray(history)) {
    throw new Error('Decision history returned a non-array payload');
  }

  if (history.length > limit) {
    throw new Error(`Decision history returned ${history.length} rows, expected at most ${limit}`);
  }

  const allowed = new Set(entityIds);
  for (const row of history) {
    if (row.entity_id && !allowed.has(String(row.entity_id))) {
      throw new Error(`Decision history returned nonmatching entity_id ${row.entity_id}`);
    }
  }
}

function resolvePlaywrightCommand() {
  if (process.platform === 'win32') {
    return 'playwright.cmd';
  }

  return 'playwright';
}

function runPlaywright(operationsWebBaseUrl) {
  return new Promise((resolve, reject) => {
    const child = spawn(resolvePlaywrightCommand(), ['test', 'tests/browser-shell.pm-live-data.smoke.spec.ts'], {
      cwd: APP_ROOT,
      env: {
        ...process.env,
        OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL: operationsWebBaseUrl,
      },
      stdio: 'inherit',
      shell: process.platform === 'win32',
    });

    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
        return;
      }

      reject(new Error(`Playwright PM live-data smoke failed with exit code ${code ?? 'unknown'}`));
    });
  });
}

async function main() {
  let parsed;

  try {
    parsed = parseArgs(process.argv.slice(2));
  } catch (error) {
    printUsage();
    throw error;
  }

  if (parsed.help) {
    printUsage();
    return;
  }

  const operationsWebBaseUrl = normalizeBaseUrl(
    parsed['operations-web-base-url'] ?? process.env.OPERATIONS_WEB_BASE_URL ?? DEFAULT_OPERATIONS_WEB_BASE_URL,
  );
  const mutationSeamBaseUrl = normalizeBaseUrl(
    parsed['mutation-seam-base-url'] ?? process.env.MUTATION_SEAM_BASE_URL ?? DEFAULT_MUTATION_SEAM_BASE_URL,
  );
  const timeoutMs = Number(parsed['timeout-ms'] ?? process.env.OPERATIONS_WEB_SMOKE_TIMEOUT_MS ?? '15000');

  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new Error(`Invalid timeout value: ${parsed['timeout-ms'] ?? process.env.OPERATIONS_WEB_SMOKE_TIMEOUT_MS}`);
  }

  console.log(`PM_LIVE_DATA_STEP mutation-seam ${mutationSeamBaseUrl.href}`);
  await expectJson(new URL('health', mutationSeamBaseUrl), 'mutation seam health', timeoutMs);
  await expectJson(new URL('api/v1/schedule/projects', mutationSeamBaseUrl), 'mutation seam schedule projects', timeoutMs);
  await expectJson(new URL('api/v1/reads/approval-queue', mutationSeamBaseUrl), 'mutation seam approval queue', timeoutMs);
  const workfront = await expectJson(new URL('api/v1/reads/pm-workfront', mutationSeamBaseUrl), 'mutation seam PM workfront', timeoutMs);
  assertPmWorkfront(workfront);
  const decisionEntityIds = collectWorkfrontEntityIds(workfront);
  const historyUrl = decisionHistoryUrl(mutationSeamBaseUrl, decisionEntityIds);
  const history = await expectJson(historyUrl, 'mutation seam PM decision history', timeoutMs);
  if (decisionEntityIds.length) {
    assertDecisionHistory(history, decisionEntityIds);
  } else if (history.length !== 0) {
    throw new Error(`No-op PM decision history smoke returned ${history.length} rows`);
  }
  console.log(
    `PM_LIVE_DATA_STEP decision-history entity_ids=${decisionEntityIds.length} rows=${history.length}`
  );

  console.log(`PM_LIVE_DATA_STEP operations-web ${operationsWebBaseUrl.href}`);
  await expectHtml(new URL('pm-review', operationsWebBaseUrl), 'operations-web PM drivers route', timeoutMs);
  await expectHtml(new URL('pm-review/workfront', operationsWebBaseUrl), 'operations-web PM workfront route', timeoutMs);

  console.log(`PM_LIVE_DATA_STEP playwright ${operationsWebBaseUrl.href}`);
  await runPlaywright(operationsWebBaseUrl.href.replace(/\/$/, ''));

  console.log(
    `PM_LIVE_DATA_SUMMARY failed=0 operations_web_base_url=${operationsWebBaseUrl.href} mutation_seam_base_url=${mutationSeamBaseUrl.href}`
  );
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`PM_LIVE_DATA_FATAL ${message}`);
  process.exitCode = 1;
});
