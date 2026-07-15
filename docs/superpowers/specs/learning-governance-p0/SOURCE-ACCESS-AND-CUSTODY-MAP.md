# Learning Source Access And Custody Map

Date: 2026-07-14

Status: VERIFIED LOCATION MAP - NO SOURCE-BODY OR RIGHTS AUTHORIZATION

## Purpose

Map the Windows Box source tree to its read-only Olares inspection surface so a
goal can bind one source identity across hosts without copying source bodies into
the platform repository.

## Verified Mapping

| Surface | Root |
|---|---|
| Windows source | `C:\Users\jjswe\Box\APEX Platform` |
| Windows UNC | `\\100.64.0.4\APEX-Platform-RO` |
| SMB | `//100.64.0.4/APEX-Platform-RO` |
| Olares read-only mount | `/mnt/apex-platform-ro` |

The Olares surface was verified as CIFS over SMB 3.1.1 with `ro` and `seal`
mount options. A write-permission check returned false. The active platform and
learning-governance Git worktrees remain separate writable implementation
surfaces.

## Path Translation

| Windows path | Olares inspection path |
|---|---|
| `C:\Users\jjswe\Box\APEX Platform\neta-ett-study-material-structure-workrepo-2026-06-20` | `/mnt/apex-platform-ro/neta-ett-study-material-structure-workrepo-2026-06-20` |
| `C:\Users\jjswe\Box\APEX Platform\source-domains\neta-ett-study-material` | `/mnt/apex-platform-ro/source-domains/neta-ett-study-material` |

Relative locators in the learning source register resolve against the approved
workrepo root only when an active goal names that root and permits the requested
metadata or body access.

## Verification Snapshot

Metadata-only inspection confirmed:

- the structure workrepo exists on the Olares mount;
- `validation/template-extraction` exists;
- all six reported Stage 0 artifact filenames dated 2026-07-09 are present; and
- `source-domains/neta-ett-study-material` exists.

No Stage 0 artifact body, source body, draft body, PDF, image, or rendered body
was opened for this verification. Filename presence does not validate content,
hashes, readiness, or authority.

## Enforcement Rules

1. Never write, rename, delete, normalize, or generate files under
   `/mnt/apex-platform-ro`.
2. Treat Windows, UNC, SMB, and Olares paths as aliases for one custody source,
   not as independent evidence copies.
3. Record the canonical source locator plus the access surface used for a given
   evidence observation.
4. File presence does not prove lawful access, license, provenance, technical
   correctness, internal-draft status, SME acceptance, or authoring approval.
5. A metadata-only goal may inspect names, paths, stat metadata, existing hashes,
   and admitted control fields. It may not open content bodies unless the goal
   explicitly authorizes that class of access.
6. Any unexpected writable mount, source mismatch, missing root, alias conflict,
   or changed source identity returns the goal to the Program Manager.
7. Working products and governed decisions belong in approved Git worktrees or
   custody roots, never in the read-only source mirror.

## Current Effect

The mount closes the Olares source-availability uncertainty for path and filename
inspection. It does not clear any source-rights, SME, privacy, platform, render,
release, or `ET-PILOT-HOLD` gate.
