const DEFAULT_OPERATIONS_WEB_BASE_URL = 'https://operations.apexpowerops.com';
const DEFAULT_MUTATION_SEAM_BASE_URL = 'https://mutation-seam.apexpowerops.com';

const routeChecks = [
  {
    label: 'operations-web import candidate',
    path: 'pm-review/import-candidate',
    marker: 'Review exceptions before import exists',
  },
  {
    label: 'operations-web import admission plan',
    path: 'pm-review/import-admission-plan',
    marker: 'Design the import gate before it can write',
  },
];

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
    'Usage: node scripts/smoke-pm-intake-hosted.mjs [--operations-web-base-url <url>] [--mutation-seam-base-url <url>] [--timeout-ms <ms>]',
  );
}

function normalizeBaseUrl(rawBaseUrl) {
  const url = new URL(rawBaseUrl);
  url.pathname = url.pathname.endsWith('/') ? url.pathname : `${url.pathname}/`;
  return url;
}

function pmBearerToken() {
  return `Bearer ${Buffer.from(
    JSON.stringify({
      actor_id: 'pm-001',
      actor_role: 'pm',
      project_scope: ['proj-001'],
    }),
  ).toString('base64')}`;
}

async function fetchWithTimeout(url, options, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function expectHtml(url, label, marker, timeoutMs) {
  const response = await fetchWithTimeout(
    url,
    {
      headers: {
        accept: 'text/html,application/xhtml+xml',
      },
      redirect: 'follow',
    },
    timeoutMs,
  );

  const body = await response.text();
  const contentType = response.headers.get('content-type') ?? '';

  if (!response.ok) {
    throw new Error(`${label} returned HTTP ${response.status}`);
  }

  if (!contentType.includes('text/html')) {
    throw new Error(`${label} returned unexpected content-type ${contentType || '<empty>'}`);
  }

  if (!body.includes(marker)) {
    throw new Error(`${label} did not include marker "${marker}"`);
  }
}

async function expectJson(url, label, timeoutMs) {
  const response = await fetchWithTimeout(
    url,
    {
      headers: {
        accept: 'application/json',
        authorization: pmBearerToken(),
      },
      redirect: 'follow',
    },
    timeoutMs,
  );

  const body = await response.text();

  if (!response.ok) {
    throw new Error(`${label} returned HTTP ${response.status}${body ? ` body=${body.slice(0, 180)}` : ''}`);
  }

  try {
    return JSON.parse(body);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`${label} returned invalid JSON: ${message}`);
  }
}

function assertOpenApiHasIntakeReads(openApi) {
  const paths = openApi?.paths;
  if (!paths || typeof paths !== 'object') {
    throw new Error('mutation seam OpenAPI did not include a paths object');
  }

  for (const path of ['/api/v1/reads/project-import-candidate', '/api/v1/reads/project-import-admission-plan']) {
    if (!Object.prototype.hasOwnProperty.call(paths, path)) {
      throw new Error(`mutation seam OpenAPI is missing ${path}`);
    }
  }
}

function assertImportCandidate(candidate) {
  if (!candidate || typeof candidate !== 'object') {
    throw new Error('import candidate returned a non-object payload');
  }

  if (candidate.mutation_authority !== 'not_admitted') {
    throw new Error(`import candidate mutation authority is ${candidate.mutation_authority}`);
  }

  if (!candidate.candidate_id) {
    throw new Error('import candidate did not include candidate_id');
  }

  if (!candidate.source_freshness || typeof candidate.source_freshness !== 'object') {
    throw new Error('import candidate did not include source_freshness');
  }
}

function assertAdmissionPlan(plan) {
  if (!plan || typeof plan !== 'object') {
    throw new Error('import admission plan returned a non-object payload');
  }

  if (plan.mutation_authority !== 'not_admitted') {
    throw new Error(`admission plan mutation authority is ${plan.mutation_authority}`);
  }

  if (!plan.approval_record_contract || typeof plan.approval_record_contract !== 'object') {
    throw new Error('admission plan did not include approval_record_contract');
  }

  if (!Array.isArray(plan.no_go_checks)) {
    throw new Error('admission plan did not include no_go_checks');
  }
}

async function runCheck(label, failures, callback) {
  try {
    await callback();
    console.log(`PM_INTAKE_HOSTED_OK ${label}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`PM_INTAKE_HOSTED_FAIL ${label} ${message}`);
    failures.push(`${label}: ${message}`);
  }
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

  const failures = [];

  for (const routeCheck of routeChecks) {
    await runCheck(routeCheck.label, failures, () =>
      expectHtml(new URL(routeCheck.path, operationsWebBaseUrl), routeCheck.label, routeCheck.marker, timeoutMs),
    );
  }

  await runCheck('mutation seam health', failures, () =>
    expectJson(new URL('health', mutationSeamBaseUrl), 'mutation seam health', timeoutMs),
  );
  await runCheck('mutation seam OpenAPI intake read paths', failures, async () => {
    const openApi = await expectJson(new URL('openapi.json', mutationSeamBaseUrl), 'mutation seam OpenAPI', timeoutMs);
    assertOpenApiHasIntakeReads(openApi);
  });
  await runCheck('mutation seam import candidate read', failures, async () => {
    const candidate = await expectJson(
      new URL('api/v1/reads/project-import-candidate', mutationSeamBaseUrl),
      'mutation seam import candidate read',
      timeoutMs,
    );
    assertImportCandidate(candidate);
  });
  await runCheck('mutation seam import admission plan read', failures, async () => {
    const plan = await expectJson(
      new URL('api/v1/reads/project-import-admission-plan', mutationSeamBaseUrl),
      'mutation seam import admission plan read',
      timeoutMs,
    );
    assertAdmissionPlan(plan);
  });

  if (failures.length > 0) {
    console.error(
      `PM_INTAKE_HOSTED_SUMMARY failed=${failures.length} operations_web_base_url=${operationsWebBaseUrl.href} mutation_seam_base_url=${mutationSeamBaseUrl.href}`,
    );
    process.exitCode = 1;
    return;
  }

  console.log(
    `PM_INTAKE_HOSTED_SUMMARY failed=0 operations_web_base_url=${operationsWebBaseUrl.href} mutation_seam_base_url=${mutationSeamBaseUrl.href}`,
  );
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`PM_INTAKE_HOSTED_FATAL ${message}`);
  process.exitCode = 1;
});
