export type RunEnv = "sandbox" | "host";
export type RunStatus = "running" | "success" | "failure" | "canceled";

export type ToolArgs = {
  env?: RunEnv;
  service?: string;
  packet_id?: string;
  run_id?: string;
  status?: Exclude<RunStatus, "running">;
  notes?: string;
  since?: string;
};

const runEnvs = new Set<RunEnv>(["sandbox", "host"]);
const closedRunStatuses = new Set<Exclude<RunStatus, "running">>([
  "success",
  "failure",
  "canceled",
]);
const runStatuses = new Set<RunStatus>(["running", "success", "failure", "canceled"]);

function requireString(value: unknown, fieldName: string): string {
  if (typeof value !== "string") {
    throw new Error(`${fieldName} must be a non-empty string.`);
  }

  const trimmed = value.trim();

  if (!trimmed) {
    throw new Error(`${fieldName} must be a non-empty string.`);
  }

  return trimmed;
}

function optionalString(value: unknown, fieldName: string): string | undefined {
  if (value === undefined) {
    return undefined;
  }

  return requireString(value, fieldName);
}

export function requireRunEnv(value: unknown, fieldName = "env"): RunEnv {
  const env = requireString(value, fieldName) as RunEnv;

  if (!runEnvs.has(env)) {
    throw new Error(`${fieldName} must be one of: sandbox, host.`);
  }

  return env;
}

export function optionalRunEnv(value: unknown, fieldName = "env"): RunEnv | undefined {
  if (value === undefined) {
    return undefined;
  }

  return requireRunEnv(value, fieldName);
}

export function requireService(value: unknown): string {
  return requireString(value, "service");
}

export function optionalService(value: unknown): string | undefined {
  return optionalString(value, "service");
}

export function requirePacketId(value: unknown): string {
  return requireString(value, "packet_id");
}

export function optionalPacketId(value: unknown): string | undefined {
  return optionalString(value, "packet_id");
}

export function requireRunId(value: unknown): string {
  return requireString(value, "run_id");
}

export function requireClosedRunStatus(
  value: unknown,
  fieldName = "status",
): Exclude<RunStatus, "running"> {
  const status = requireString(value, fieldName) as Exclude<RunStatus, "running">;

  if (!closedRunStatuses.has(status)) {
    throw new Error(`${fieldName} must be one of: success, failure, canceled.`);
  }

  return status;
}

export function optionalRunStatus(value: unknown, fieldName = "status"): RunStatus | undefined {
  if (value === undefined) {
    return undefined;
  }

  const status = requireString(value, fieldName) as RunStatus;

  if (!runStatuses.has(status)) {
    throw new Error(`${fieldName} must be one of: running, success, failure, canceled.`);
  }

  return status;
}

export function optionalSince(value: unknown): string | undefined {
  if (value === undefined) {
    return undefined;
  }

  const since = requireString(value, "since");
  const normalized = new Date(since);

  if (Number.isNaN(normalized.getTime())) {
    throw new Error("since must be a valid ISO-8601 timestamp.");
  }

  return normalized.toISOString();
}