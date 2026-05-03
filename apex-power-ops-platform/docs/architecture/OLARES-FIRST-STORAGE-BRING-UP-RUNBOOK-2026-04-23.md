# Olares First Storage Bring-Up Runbook

Date: 2026-04-23
Status: Active bounded rerun source
Scope: storage, backup, and restore validation for the first Olares workstation lane

## Purpose

This runbook preserves the bounded rerun path for storage and backup validation.

It does not authorize broad host reprovisioning.

## Current Evidence Floor

1. `infra/olares/scripts/storage-first-run.sh`
2. `infra/olares/scripts/storage-first-run.env.template`
3. `docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`
4. `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`

## Rerun Steps

1. copy `infra/olares/scripts/storage-first-run.env.template` into a machine-local session env file outside normal repo publication scope
2. replace every placeholder value in that session env file before executing the storage script
3. run `infra/olares/scripts/storage-first-run.sh <session-env-file>` from a normal operator account with sudo access on the target Linux host
4. confirm the script can still validate required commands, initialize the labeled filesystems, and initialize local plus offsite Restic repositories without manual divergence from the script body
5. record any material backup or restore drift in a dated handoff instead of editing the post-closure checklist ad hoc

## Exit Condition

Storage rerun readiness remains valid when the governed script and env template
remain sufficient to re-establish the bounded local and offsite backup posture
without inventing new first-run steps.
