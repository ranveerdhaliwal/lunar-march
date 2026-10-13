---
name: lunar-march
description: Coordinate bounded Luna or OpenCode work and retain durable evidence for risky or resumable projects. Use when independent work or recovery justifies delegation; do not select it merely because a task spans several files.
license: MIT
metadata:
  short-description: Bounded delegation with optional durable evidence
---

# LunarMarch

If you are already a delegated worker with a bounded assignment, execute that assignment and return evidence. Do not select a mode, read orchestration references, or start another agent.

Choose the shortest path to the user's acceptance criteria. A cheaper worker does not make a longer workflow cheaper. The parent owns scope, decisions, integration, and acceptance.

## Choose the execution path

- **Direct:** keep small or tightly dependent work in the parent. No workers, run state, or extra review ritual for a routine edit that the parent can verify directly.
- **Quick (ordinary delegation):** one bounded worker, targeted checks, then parent review of its result. A parent that did not implement the change is the independent reviewer. No separate Reviewer, Scout, Tester, Auditor, or durable state unless it adds necessary evidence.
- **Research:** usually one Scout; use two only for genuinely independent questions. One synthesis, no nested delegation.
- **Task (durable):** use the launcher when immutable evidence, write boundaries, or recovery matters. Builder, checks, independent Reviewer, parent acceptance. One Fixer and one re-review only for concrete material defects.
- **March:** reserve phased freezes and Auditors for meaningful cross-task integration or high-risk boundaries. A project with several files does not automatically need March.

Before delegating, identify what the worker removes from the parent: independent work that can overlap, a large context to compress, or a required specialist/evidence boundary. If the parent will read the same inputs, wait, and redo the same checks, use Direct. A complete bounded assignment can be dispatched immediately without a parent reconnaissance pass. Use the host's native worker tool when available. In a scripted workflow with a fully resolved packet, launch the worker deterministically and invoke the parent for acceptance after success; do not pay for a model turn just to start a fixed command. A failed startup needs launcher diagnosis, not a review agent.

Start native delegation with no inherited turns and one compact packet: objective, exact inputs and owned paths, constraints, deliverable, and acceptance checks. Files carry the context. Do not load every reference or scan the whole repository for every role. Prefer native workers when the host can explicitly bind the required model and sandbox; keep existing model/effort defaults until measured evidence supports changing them. See [references/routing.md](references/routing.md) for routing or escalation.

## Bound the work

- State what counts as done before dispatch. Optional improvements do not reopen accepted work.
- Use one writer; add independent read-only lanes only when they can reduce elapsed time. Workers never spawn workers.
- Review concrete changed behavior and protected invariants. Ask the worker for changed paths, exact check commands/results, and unresolved requirements. Reuse recorded checks only when they are bound to the unchanged files being reviewed; add targeted probes for uncovered behavior. Passing tests do not excuse an unmet requirement.
- After one repair cycle, the parent adjudicates unresolved findings. Do not rotate roles, invent replacement tasks, or add Auditors to evade a budget.
- Durable defaults: four reservations per task, two Reviewer attempts, two Auditor attempts, and 24 reservations per run. Count infrastructure failures too. Set larger ceilings before registration only when scope justifies them. Ceilings bound attempts, not tokens or minutes.
- Keep reports around 300 words, with decisive paths, checks, concrete findings, and remaining uncertainty. Put logs in files. Wait for meaningful worker events rather than repeatedly polling unchanged state.

## Evidence and acceptance

Every delegated mutation needs review by a context that did not implement it. The parent can provide that review for Quick. Durable Task/March acceptance additionally requires a hash-bound Reviewer or Auditor attempt. Mechanical gates prove source and lifecycle integrity, not semantic correctness. Preserve authorization and declared write scope.

Use terminal telemetry as the usage authority. Report available total tokens and uncached input plus output, including failed attempts. Missing usage is `not reported`, never zero. Parent/native usage may be unavailable to the launcher, so reported worker totals are not whole-workflow costs. Never use the Unicode em dash character (U+2014) in LunarMarch reports.

For durable work, read [references/contracts.md](references/contracts.md) and [references/modes.md](references/modes.md). Read [references/long-runs.md](references/long-runs.md) only for phases or recovery. Never edit state, reservations, frozen artifacts, or gates by hand.

```bash
python3 <skill>/scripts/lunarmarch.py init --project-root <project> --run-root <run> --goal "<goal>" --mode task --max-attempts 8
python3 <skill>/scripts/lunarmarch.py add-task --run-root <run> --spec <contract.json>
python3 <skill>/scripts/lunarmarch.py launch --run-root <run> --task-id <task> --role builder --run-checks
python3 <skill>/scripts/lunarmarch.py status --run-root <run>
```

After clean independent review, record parent acceptance with `accept --run-root <run> --task-id <task> --attempt <review-attempt>`.

For provider selection read [references/providers.md](references/providers.md); for installation read [references/installation.md](references/installation.md). For audits read [references/testing-and-evaluation.md](references/testing-and-evaluation.md). Read [references/context-evaluation.md](references/context-evaluation.md) before changing model, effort, or context policy based on performance claims. The [2026-10-10 efficiency audit](references/efficiency-audit-2026-10-10.md) records the observed overhead and candidate workflow changes; the measured multi-file pilot favored Direct. See [workflow results](evals/workflow-efficiency/results/2026-10-10-direct-v-quick.md) before claiming savings.

Stop launching on exhausted budgets, unknown active writers, missing authority, or inaccessible required systems. Preserve incomplete work honestly. Resolve ordinary worker failure within the bounded route when possible; do not turn every adjudication into a human approval request.
