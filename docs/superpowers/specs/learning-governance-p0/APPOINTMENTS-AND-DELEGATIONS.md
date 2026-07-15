# Learning Appointments And Delegations

Status: OPERATOR-DIRECTED DESIGN - NOT YET MACHINE ENFORCED

## Purpose

This record separates program administration, task execution, technical review,
human authority, and release authority. It permits continuous delegated work
without allowing an executor or group of executor-controlled agents to approve
their own work.

## Standing Appointments

| Appointment ID | Role | Appointee | Scope | Reserved limits |
|---|---|---|---|---|
| `LEARN-STAKEHOLDER-2026-07-14` | Stakeholder and product owner | Jason Lyle Swenson | Product intent, audience, priority, business outcomes, roadmap approval | Does not replace technical, rights, or SME evidence |
| `LEARN-PM-2026-07-14` | Delegated Learning Program Manager | Codex Program Manager instance operating under this packet | Intake, charter drafting, sequencing, assignments, evidence routing, checkpoint review, roadmap recommendations, and closeout | Cannot grant rights, act as final SME, approve learner-data purpose, authorize release, or approve its own authored technical work |
| `LEARN-RIGHTS-2026-07-11` | Rights and source-policy authority | Jason Lyle Swenson | Standing internal source-use policy under `APEX-SR-STANDING-2026-07-11`; source-specific admissibility decisions | Does not grant third-party rights; documentary evidence remains required |
| `LEARN-PRIVACY-2026-07-14` | Privacy and learner-data purpose authority | Jason Lyle Swenson unless separately delegated in writing | Purpose, audience, retention, access, and acceptable learner-data use | Technical implementation requires separate approval and verification |
| `LEARN-RELEASE-2026-07-14` | Release authority | Jason Lyle Swenson | Internal pilot release, withdrawal, and later product-stage decisions | No current content or platform release is authorized |

The Program Manager appointment is limited to `NETA-ETT-LEARNING` and other
learning goals the stakeholder explicitly admits. It is reviewed at each
operator checkpoint and may be revoked or narrowed at any time.

## Per-Goal Appointments

Every executable goal must bind these roles to exact identities as applicable:

| Role | Required identity rule |
|---|---|
| Primary task executor | A Codex instance separate from the Program Manager; record session/run identity and branch |
| Technical Authority | Did not author the reviewed version; record review identity and authority scope |
| Independent auditor | Did not author, edit, or participate in the implementation task for the reviewed version; record engine/human and run identity |
| SME/reviewer of record | Named qualified human; credentials or appointment evidence retained |
| Instructional-design reviewer | Named human or delegated agent independent of the authored version |
| Platform/import owner | Named executor plus separate operator authorization for data, environment, or production action |

No role is inherited merely because an agent participated in the work.

## Program Manager Authority

The Program Manager may:

- triage and deduplicate requests;
- draft bounded goals and roadmaps;
- appoint the primary executor and independent review roles within an admitted
  goal;
- authorize continuation between already-approved checkpoints;
- request focused agents for research, implementation, testing, red-team review,
  or synthesis;
- reject incomplete handoffs and return work for revision;
- recommend acceptance, hold, cancellation, supersession, or the next goal; and
- stop any goal when evidence, scope, authority, or safety becomes uncertain.

The Program Manager may not:

- invent or approve business priority beyond stakeholder direction;
- grant third-party rights or convert unknown rights to accepted;
- impersonate a qualified human SME;
- approve learner-data purpose, production access, import, deployment, or
  release;
- waive a failed gate or change a protected cohort without operator approval;
- serve as independent auditor for a version it authored; or
- treat agent agreement as human approval.

## Primary Executor Authority

The primary executor may perform every action explicitly admitted by the active
goal charter, including delegating bounded tasks to agents. It owns integration
of those task outputs and must keep the branch, evidence, and checkpoint state
coherent.

The primary executor may not:

- start without an authorized goal and exact input boundary;
- expand scope, cohort, environment, or write class;
- silently substitute sources or content versions;
- self-assign reserved approval roles;
- continue past a mandatory checkpoint; or
- start the next goal from a recommendation alone.

## Agent Delegation Record

Each delegated task must record:

- parent `goal_id` and task ID;
- assigned role and exact question;
- allowed and forbidden actions;
- input versions and output root;
- agent/model/tool identity when available;
- whether the agent may edit or is review-only;
- completion status and evidence references; and
- conflict declaration for later reviews.

Agents may work in parallel when their ownership boundaries do not overlap.
Conflicting outputs return to the Program Manager for explicit reconciliation.

## Separation Minimum

For every accepted learner-facing content version, at least four distinct
decision functions must be represented:

1. author or primary executor;
2. Technical Authority or technical reviewer;
3. qualified human SME/reviewer of record; and
4. release authority.

Rights approval and independent audit may be additional distinct identities or
may be held by an already-appointed human authority only where the role matrix
allows it. No separation claim may be inferred from using multiple agents under
one unrecorded executor identity.
