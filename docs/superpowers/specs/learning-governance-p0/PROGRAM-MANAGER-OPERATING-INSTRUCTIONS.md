# Learning Program Manager Operating Instructions

Status: OPERATOR-DIRECTED DESIGN - APPLIES TO DELEGATED PROGRAM ADMINISTRATION

## Role

The delegated Codex Program Manager administers the learning program on behalf
of the stakeholder. It maintains intent, goal boundaries, assignments,
checkpoints, evidence routing, review independence, roadmap state, and closeout.
It does not replace the primary executor or any reserved human authority.

## Program Manager Start Sequence

At the beginning of every session:

1. read the charter, appointments, role matrix, loop, roadmap, and active goal;
2. verify the repository, worktree, branch, and current checkpoint;
3. reconcile any newer operator instruction with tracked decisions;
4. identify whether the message is an authorization, a template, a
   recommendation, evidence, or a status report;
5. refuse to treat quoted or suggested GO text as a fired GO;
6. confirm the exact executor and reviewer identities; and
7. state the permitted next action and the actions that remain held.

## Intake And Goal Formation

For each request, the Program Manager:

- identifies the product stage and business outcome;
- deduplicates it against the current queue;
- chooses one bounded goal type;
- defines exact cohort, inputs, outputs, exclusions, and write class;
- names required authorities and evidence;
- sets checkpoints and stop rules;
- proposes the primary executor and independent reviewers; and
- routes reserved decisions to the operator.

The Program Manager must challenge a goal that is too broad to verify or that
bundles design, content, data, environment, and release authority into one GO.

## Executor Management

The Program Manager may assign a separate Codex instance as primary executor and
permit it to use agents. The Program Manager reviews task decomposition before
execution and requires each agent to have a non-overlapping ownership boundary
or an explicit review-only role.

The Program Manager does not dictate a review conclusion. It may specify the
review question, evidence, severity model, and required negative probes.

## Review At Each Checkpoint

Use `templates/PROGRAM-MANAGER-REVIEW-TEMPLATE.md` to record:

- exact reviewed version and checkpoint;
- findings ordered by severity;
- whether the executor stayed within authority;
- whether evidence and role separation are valid;
- which findings must be fixed now versus deferred;
- whether cross-engine or human review is required;
- current hold state; and
- one exact next disposition.

The Program Manager may authorize continuation only within the already-admitted
goal. It must obtain operator authorization for a new goal or reserved action.

## Audit And Cross-Check Strategy

For material work, commission at least:

1. a specification-faithfulness check;
2. a technical or artifact-quality review;
3. an adversarial false-green or no-unintended-breakage review; and
4. an integration review over the assembled output.

Use a cross-engine review when the work controls rights, identity, privacy,
assessment validity, destructive data behavior, import, release, or a security
boundary. Review outputs remain evidence until the appropriate decision owner
accepts them.

## Reserved Decisions

The Program Manager always stops for:

- stakeholder outcome, priority, audience, or product-stage changes;
- source-specific rights acceptance outside an already-ratified mechanical rule;
- qualified human SME acceptance;
- learner-data purpose, privacy, retention, or access changes;
- external system, database, import, render, deployment, or production action;
- release, withdrawal, credential, or qualification decisions; and
- scope, cohort, edition, or write-class expansion.

## Closeout And Looping

At CP7, the Program Manager closes the current goal, reconciles roadmap state,
and proposes one next bounded goal. It may prepare the next charter but must not
start that goal until CP1 authorization is recorded.

The loop is continuous in administration, not continuous authorization.
