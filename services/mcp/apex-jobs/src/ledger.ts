import type { RunEnv, RunStatus } from "./validation.js";

export type LedgerRun = {
  run_id: string;
  env: RunEnv;
  service: string;
  packet_id?: string;
  status: RunStatus;
  created_at: string;
  notes?: string;
  completed_at?: string;
};

export type LedgerPromotion = {
  packet_id: string;
  promoted_at: string;
  supporting_run_ids: string[];
};

export type Ledger = {
  runs: LedgerRun[];
  promotions: LedgerPromotion[];
};

export type RunFilter = {
  env?: RunEnv;
  service?: string;
  packet_id?: string;
  status?: RunStatus;
  since?: string;
};

export function createRunId(now = Date.now, random = Math.random): string {
  return `${now()}-${random().toString(36).slice(2, 10)}`;
}

export function requireOpenRun(run: LedgerRun | undefined, runId: string): LedgerRun {
  if (!run) {
    throw new Error(`Run not found: ${runId}`);
  }

  if (run.status !== "running" || run.completed_at) {
    throw new Error(`Run ${runId} is already closed and cannot be modified.`);
  }

  return run;
}

export function closeRun(
  run: LedgerRun,
  status: Exclude<RunStatus, "running">,
  notes: string | undefined,
  nowIso: () => string = () => new Date().toISOString(),
): LedgerRun {
  run.status = status;
  run.notes = notes;
  run.completed_at = nowIso();
  return run;
}

export function filterRuns(runs: LedgerRun[], filter: RunFilter): LedgerRun[] {
  return runs.filter((run) => {
    if (filter.env && run.env !== filter.env) return false;
    if (filter.service && run.service !== filter.service) return false;
    if (filter.packet_id && run.packet_id !== filter.packet_id) return false;
    if (filter.status && run.status !== filter.status) return false;
    if (filter.since && run.created_at < filter.since) return false;
    return true;
  });
}

export function createPromotion(
  ledger: Ledger,
  packetId: string,
  nowIso: () => string = () => new Date().toISOString(),
): LedgerPromotion {
  const supportingRuns = ledger.runs.filter(
    (run) => run.packet_id === packetId && run.env === "host" && run.status === "success",
  );

  if (supportingRuns.length === 0) {
    throw new Error(`Packet ${packetId} cannot be promoted: no successful env=host run is on record.`);
  }

  const promotion: LedgerPromotion = {
    packet_id: packetId,
    promoted_at: nowIso(),
    supporting_run_ids: supportingRuns.map((run) => run.run_id),
  };

  ledger.promotions.push(promotion);
  return promotion;
}