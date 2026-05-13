import assert from "node:assert/strict";
import test from "node:test";

import { closeRun, createPromotion, filterRuns, requireOpenRun } from "../build/ledger.js";

test("closeRun records a final status and completion timestamp", () => {
  const run = {
    run_id: "run-123",
    env: "sandbox",
    service: "ai-workflow",
    packet_id: "packet-123",
    status: "running",
    created_at: "2026-05-13T12:00:00.000Z",
  };

  const closed = closeRun(run, "success", "verification passed", () => "2026-05-13T12:05:00.000Z");

  assert.equal(closed, run);
  assert.equal(run.status, "success");
  assert.equal(run.notes, "verification passed");
  assert.equal(run.completed_at, "2026-05-13T12:05:00.000Z");
});

test("requireOpenRun refuses missing runs", () => {
  assert.throws(
    () => requireOpenRun(undefined, "missing-run"),
    /Run not found: missing-run/,
  );
});

test("requireOpenRun refuses a run that already has a closed status", () => {
  const run = {
    run_id: "run-closed",
    env: "host",
    service: "ai-workflow",
    packet_id: "packet-123",
    status: "success",
    created_at: "2026-05-13T12:00:00.000Z",
    completed_at: "2026-05-13T12:05:00.000Z",
  };

  assert.throws(
    () => requireOpenRun(run, run.run_id),
    /already closed and cannot be modified/,
  );
});

test("requireOpenRun refuses a run once closeRun has finalized it", () => {
  const run = {
    run_id: "run-finalized",
    env: "host",
    service: "ai-workflow",
    packet_id: "packet-123",
    status: "running",
    created_at: "2026-05-13T12:00:00.000Z",
  };

  closeRun(run, "failure", "operator rejected", () => "2026-05-13T12:03:00.000Z");

  assert.throws(
    () => requireOpenRun(run, run.run_id),
    /already closed and cannot be modified/,
  );
});

test("filterRuns applies since and status filters", () => {
  const runs = [
    {
      run_id: "run-early",
      env: "sandbox",
      service: "ai-workflow",
      packet_id: "packet-123",
      status: "success",
      created_at: "2026-05-13T11:59:00.000Z",
      completed_at: "2026-05-13T12:00:00.000Z",
    },
    {
      run_id: "run-late",
      env: "host",
      service: "ai-workflow",
      packet_id: "packet-123",
      status: "success",
      created_at: "2026-05-13T12:01:00.000Z",
      completed_at: "2026-05-13T12:02:00.000Z",
    },
    {
      run_id: "run-running",
      env: "host",
      service: "other-service",
      packet_id: "packet-999",
      status: "running",
      created_at: "2026-05-13T12:03:00.000Z",
    },
  ];

  const filtered = filterRuns(runs, {
    service: "ai-workflow",
    status: "success",
    since: "2026-05-13T12:00:00.000Z",
  });

  assert.deepEqual(
    filtered.map((run) => run.run_id),
    ["run-late"],
  );
});

test("createPromotion refuses packets without successful host evidence", () => {
  const ledger = {
    runs: [
      {
        run_id: "run-sandbox",
        env: "sandbox",
        service: "ai-workflow",
        packet_id: "packet-123",
        status: "success",
        created_at: "2026-05-13T12:00:00.000Z",
        completed_at: "2026-05-13T12:01:00.000Z",
      },
    ],
    promotions: [],
  };

  assert.throws(
    () => createPromotion(ledger, "packet-123"),
    /no successful env=host run is on record/,
  );
  assert.equal(ledger.promotions.length, 0);
});

test("createPromotion records the supporting successful host runs", () => {
  const ledger = {
    runs: [
      {
        run_id: "run-host-1",
        env: "host",
        service: "ai-workflow",
        packet_id: "packet-123",
        status: "success",
        created_at: "2026-05-13T12:00:00.000Z",
        completed_at: "2026-05-13T12:01:00.000Z",
      },
      {
        run_id: "run-host-2",
        env: "host",
        service: "ai-workflow",
        packet_id: "packet-123",
        status: "success",
        created_at: "2026-05-13T12:02:00.000Z",
        completed_at: "2026-05-13T12:03:00.000Z",
      },
      {
        run_id: "run-other",
        env: "host",
        service: "ai-workflow",
        packet_id: "packet-other",
        status: "success",
        created_at: "2026-05-13T12:04:00.000Z",
        completed_at: "2026-05-13T12:05:00.000Z",
      },
    ],
    promotions: [],
  };

  const promotion = createPromotion(ledger, "packet-123", () => "2026-05-13T12:06:00.000Z");

  assert.deepEqual(promotion, {
    packet_id: "packet-123",
    promoted_at: "2026-05-13T12:06:00.000Z",
    supporting_run_ids: ["run-host-1", "run-host-2"],
  });
  assert.deepEqual(ledger.promotions, [promotion]);
});