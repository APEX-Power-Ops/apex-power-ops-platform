-- jobs domain — indexes (requires 002). FK-join + queue-ordering + open-gate.
CREATE INDEX idx_job_status      ON jobs.job (status);
CREATE INDEX idx_job_priority    ON jobs.job (priority, dispatch_id);
CREATE INDEX idx_job_predecessor ON jobs.job (predecessor_id);
CREATE INDEX idx_run_job         ON jobs.run (job_id);
CREATE INDEX idx_gate_job        ON jobs.gate (job_id);
CREATE INDEX idx_gate_open       ON jobs.gate (job_id) WHERE state = 'pending';
