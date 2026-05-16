const routeChecks = [
  { path: '/', marker: 'Validation Surface' },
  { path: '/integration-dashboard/index.html', marker: 'APEX Cross-Surface Integration Test Dashboard' },
  { path: '/lead-ops/index.html', marker: 'APEX Lead Surface' },
  { path: '/pm-review/index.html', marker: 'APEX PM Drivers Review' },
  { path: '/pm-review/approval-surface.html', marker: 'APEX PM Approval Surface' },
  { path: '/pm-review/schedule.html', marker: 'APEX PM Schedule Review' },
  { path: '/pm-review/tracer.html', marker: 'APEX PM Upstream Tracer Review' },
  { path: '/pm-review/variance.html', marker: 'APEX PM Variance Review' },
  { path: '/pm-review/import-candidate', marker: 'Review exceptions before import exists' },
  { path: '/pm-review/import-admission-plan', marker: 'Design the import gate before it can write' },
  { path: '/pm-review/import-approval-readiness', marker: 'Review the approval gate before it can persist' },
  { path: '/pm-review/import-intake', marker: 'Run Project Miner intake from one workbench' },
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
  console.log('Usage: node scripts/smoke-hosted-routes.mjs --base-url <url> [--timeout-ms <ms>]');
}

function normalizeBaseUrl(rawBaseUrl) {
  const url = new URL(rawBaseUrl);
  url.pathname = url.pathname.endsWith('/') ? url.pathname : `${url.pathname}/`;
  return url;
}

async function fetchRoute(baseUrl, timeoutMs, routeCheck) {
  const targetUrl = new URL(routeCheck.path.replace(/^\//, ''), baseUrl);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(targetUrl, {
      headers: {
        accept: 'text/html,application/xhtml+xml',
      },
      redirect: 'follow',
      signal: controller.signal,
    });
    const body = await response.text();
    const contentType = response.headers.get('content-type') ?? '';

    if (!response.ok) {
      throw new Error(`Expected HTTP 200-range response, received ${response.status}`);
    }

    if (!contentType.includes('text/html')) {
      throw new Error(`Expected HTML response, received content-type ${contentType || '<empty>'}`);
    }

    if (!body.includes(routeCheck.marker)) {
      throw new Error(`Expected marker "${routeCheck.marker}" was not found in the response body`);
    }

    console.log(`SMOKE_OK ${routeCheck.path} status=${response.status} marker="${routeCheck.marker}"`);
    return null;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`SMOKE_FAIL ${routeCheck.path} ${message}`);
    return { path: routeCheck.path, message };
  } finally {
    clearTimeout(timeout);
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

  const rawBaseUrl = parsed['base-url'] ?? process.env.OPERATIONS_WEB_BASE_URL;

  if (!rawBaseUrl) {
    printUsage();
    throw new Error('A hosted base URL is required via --base-url or OPERATIONS_WEB_BASE_URL.');
  }

  const timeoutMs = Number(parsed['timeout-ms'] ?? process.env.OPERATIONS_WEB_SMOKE_TIMEOUT_MS ?? '15000');

  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new Error(`Invalid timeout value: ${parsed['timeout-ms'] ?? process.env.OPERATIONS_WEB_SMOKE_TIMEOUT_MS}`);
  }

  const baseUrl = normalizeBaseUrl(rawBaseUrl);
  const failures = [];

  for (const routeCheck of routeChecks) {
    const failure = await fetchRoute(baseUrl, timeoutMs, routeCheck);
    if (failure) {
      failures.push(failure);
    }
  }

  if (failures.length > 0) {
    console.error(`SMOKE_SUMMARY failed=${failures.length} passed=${routeChecks.length - failures.length} base_url=${baseUrl.href}`);
    process.exitCode = 1;
    return;
  }

  console.log(`SMOKE_SUMMARY failed=0 passed=${routeChecks.length} base_url=${baseUrl.href}`);
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`SMOKE_FATAL ${message}`);
  process.exitCode = 1;
});
