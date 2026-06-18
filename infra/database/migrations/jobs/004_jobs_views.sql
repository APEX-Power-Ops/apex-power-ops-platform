-- jobs domain — the claim-eligibility view (requires 002).
-- A job is claimable iff: status=pending AND (no predecessor OR predecessor
-- succeeded) AND it has no open (pending) human-approval gate. Ordered the way
-- claim() consumes it: priority asc, then dispatch_id asc (deterministic).
CREATE OR REPLACE VIEW jobs.v_eligible AS
SELECT j.*
FROM jobs.job j
WHERE j.status = 'pending'
  AND (j.predecessor_id IS NULL
       OR EXISTS (SELECT 1 FROM jobs.job p
                  WHERE p.id = j.predecessor_id AND p.status = 'succeeded'))
  AND NOT EXISTS (SELECT 1 FROM jobs.gate g
                  WHERE g.job_id = j.id AND g.state = 'pending')
ORDER BY j.priority ASC, j.dispatch_id ASC;
