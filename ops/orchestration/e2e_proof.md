# apex-jobs — end-to-end proof (Olares host, 2026-06-18)

Recorded run of the orchestration layer against the live `orchestration_dev`
ledger on the host PG17 dev-pg. Demonstrates the full path: enqueue → claim
(`FOR UPDATE SKIP LOCKED`) → env & human-approval gates → subprocess run →
run/promotion ledger. Built + tested via TDD in `orchestration/chip3-apex-jobs`.

## 1. Canary — happy path (env=sandbox, no gate)

```
$ apex-jobs enqueue --dispatch-id 2026-06-18-canary --title "orchestration canary" \
    --env-required sandbox --payload '{"command":"echo canary-ok"}'
1eb0edc7-13da-4ee8-a80d-a6731ab79cc8

$ apex-jobs queue
 100  2026-06-18-canary  orchestration canary  -> any

$ python -c "from apex_jobs.worker import run_once; print(run_once(as_='cc', env='sandbox'))"
{'job': '2026-06-18-canary', 'run': 'a2020f88-...', 'status': 'succeeded', 'exit_code': 0}

$ apex-jobs status 2026-06-18-canary
succeeded
$ apex-jobs ledger 2026-06-18-canary
attempt 1  env=sandbox  succeeded  exit=0  by=cc
```

## 2. Gated ops-replay — env=host + requires_approval (gate_category=schema)

The real dogfood: the job's payload applies the `work`-domain foundation
migrations (001–005) to `ops_dev` — a schema mutation, so it is gated.

```
$ apex-jobs enqueue --dispatch-id 2026-06-18-ops-replay-work-foundation \
    --title "replay work/001-005 -> ops_dev" \
    --env-required host --requires-approval --gate-category schema \
    --payload '{"command":"for f in 001_work_enums 002_work_tables 003_work_indexes \
        004_work_triggers_and_functions 005_work_views; do PGPASSWORD=*** psql ... \
        -d ops_dev -f .../work/$f.sql || exit 1; done"}'
da76575c-...

# BEFORE approval — the human gate blocks at the queue boundary:
$ apex-jobs queue
(no eligible jobs)
$ python -c "from apex_jobs.worker import run_once; print(run_once(as_='cc', env='host'))"
None                        # not claimable while the gate is open

$ apex-jobs gates --job 2026-06-18-ops-replay-work-foundation
88dc8407-...   schema   pending

# OPERATOR approves:
$ apex-jobs approve --gate 88dc8407-... --by operator
88dc8407-...

# AFTER approval — worker claims, runs (env=host), reports:
$ python -c "from apex_jobs.worker import run_once; print(run_once(as_='cc', env='host'))"
{'job': '2026-06-18-ops-replay-work-foundation', 'run': 'aeda6468-...',
 'status': 'succeeded', 'exit_code': 0}
$ apex-jobs ledger 2026-06-18-ops-replay-work-foundation
attempt 1  env=host  succeeded  exit=0  by=cc
```

### Result — `ops_dev` work schema built through the bus
```
$ psql -d ops_dev -c "\dt work.*"   (13 objects: 8 tables + 5 views)
work.assignments        work.projects            work.v_progress_current
work.dependencies       work.tasks               work.v_task_schedule
work.execution_issues   work.wbs_nodes           work.v_wbs_hierarchy
work.progress_snapshots work.work_packages       work.v_work_package_status
                                                  work.v_execution_issue_dashboard
```

This closes the pending Chip‑1 `ops_dev` foundation replay — executed *through*
the orchestration layer, with both the env gate (host) and the human gate
(schema approval) enforced and the run recorded in the ledger.

> NOTE: `work/006`–`012` and the org/identity FK activations (`007`/`008`,
> which need seed data) remain a follow-on; this proof applied the self-contained
> foundation (001–005, no hard cross-schema FKs).
