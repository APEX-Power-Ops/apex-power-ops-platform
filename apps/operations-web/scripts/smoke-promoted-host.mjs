import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(HERE, '..');
const REPO_ROOT = path.resolve(APP_ROOT, '..', '..');
const DEFAULT_PUBLIC_CONTROL_PLANE_BASE_URL = 'https://control.apexpowerops.com';

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

    if (argument === '--skip-authenticated-checks') {
      parsed.skipAuthenticatedChecks = true;
      continue;
    }

    if (argument === '--local-control-plane-runtime') {
      parsed.localControlPlaneRuntime = true;
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
    'Usage: node scripts/smoke-promoted-host.mjs --operations-web-base-url <url> --control-plane-base-url <url> [--timeout-ms <ms>] [--skip-authenticated-checks] [--local-control-plane-runtime]'
  );
}

function resolvePythonCommand() {
  if (process.env.APEX_PLATFORM_PYTHON?.trim()) {
    return process.env.APEX_PLATFORM_PYTHON.trim();
  }

  const windowsVenvPython = path.join(REPO_ROOT, '.venv', 'Scripts', 'python.exe');
  const posixVenvPython = path.join(REPO_ROOT, '.venv', 'bin', 'python');

  if (process.platform === 'win32') {
    return windowsVenvPython;
  }

  return posixVenvPython;
}

function resolvePackageManagerCommand() {
  const explicit = process.env.APEX_PLATFORM_PNPM?.trim();
  if (explicit) {
    return { command: explicit, args: [] };
  }

  if (process.platform === 'win32') {
    return {
      command: 'corepack.cmd',
      args: ['pnpm'],
    };
  }

  return {
    command: 'pnpm',
    args: [],
  };
}

function runCommand(command, args, extraEnv = {}, useShell = false) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: REPO_ROOT,
      env: {
        ...process.env,
        ...extraEnv,
      },
      stdio: 'inherit',
      shell: useShell,
    });

    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
        return;
      }

      reject(new Error(`Command failed (${code}): ${command} ${args.join(' ')}`));
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

  const operationsWebBaseUrl = parsed['operations-web-base-url'] ?? process.env.OPERATIONS_WEB_BASE_URL;
  const controlPlaneBaseUrl =
    parsed['control-plane-base-url'] ??
    process.env.OPERATIONS_WEB_CONTROL_PLANE_BASE_URL ??
    DEFAULT_PUBLIC_CONTROL_PLANE_BASE_URL;
  const timeoutMs = String(parsed['timeout-ms'] ?? process.env.OPERATIONS_WEB_SMOKE_TIMEOUT_MS ?? '15000');

  if (!operationsWebBaseUrl || !controlPlaneBaseUrl) {
    printUsage();
    throw new Error(
      'Both operations-web and control-plane base URLs are required via arguments or OPERATIONS_WEB_BASE_URL / OPERATIONS_WEB_CONTROL_PLANE_BASE_URL.'
    );
  }

  const pythonCommand = resolvePythonCommand();
  const packageManager = resolvePackageManagerCommand();
  const seamArgs = [
    path.join('apps', 'control-plane-api', 'scripts', 'smoke_deployed_control_plane.py'),
    '--base-url',
    controlPlaneBaseUrl,
    '--require-apparatus-study-route',
  ];

  if (parsed.skipAuthenticatedChecks) {
    seamArgs.push('--skip-authenticated-checks');
  }

  if (parsed.localControlPlaneRuntime) {
    seamArgs.push('--local-runtime');
  }

  console.log(`PROMOTED_HOST_STEP backend-seam ${controlPlaneBaseUrl}`);
  await runCommand(pythonCommand, seamArgs);

  console.log(`PROMOTED_HOST_STEP hosted-routes ${operationsWebBaseUrl}`);
  await runCommand(process.execPath, [
    path.join('apps', 'operations-web', 'scripts', 'smoke-hosted-routes.mjs'),
    '--base-url',
    operationsWebBaseUrl,
    '--timeout-ms',
    timeoutMs,
  ]);

  console.log(`PROMOTED_HOST_STEP browser-smoke ${operationsWebBaseUrl}`);
  await runCommand(
    packageManager.command,
    [...packageManager.args, '--filter', '@apex/operations-web', 'exec', 'playwright', 'test'],
    {
      OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL: operationsWebBaseUrl,
    },
    process.platform === 'win32',
  );

  console.log(
    `PROMOTED_HOST_SUMMARY failed=0 operations_web_base_url=${operationsWebBaseUrl} control_plane_base_url=${controlPlaneBaseUrl}`
  );
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`PROMOTED_HOST_FATAL ${message}`);
  process.exitCode = 1;
});