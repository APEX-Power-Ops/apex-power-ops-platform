# Direction: #79 lvbreakertcc contract audit (projection scope)

You are auditing a DISPOSABLE COPY of the breaker catalog in a sandbox Postgres database.
HARD RULES:
- The ONLY database you may touch is the one in $BREAKER_SANDBOX_DSN. Do not connect to prod,
  Supabase, or any other database. Do not make outbound network calls to any DB.
- Scope is PROJECTION/CONTRACT only: verify the lvbreakertcc serving contract row-by-row against
  the TCC Master Reference and the live sandbox columns; characterize the TMT F-010/011 hazard.
- This sandbox CANNOT decide calc-engine BEHAVIORAL rulings (Access TCC_NEW.accdb is the behavioral
  authority and is NOT provided here). Where a finding would require behavioral fixtures, FLAG it and
  defer — do not guess.
- Deliverables ONLY: a findings report `findings-79.md` and candidate patch SQL under
  `candidate-patches/*.sql`, applied to the sandbox DB. Never produce prod migrations directly.
