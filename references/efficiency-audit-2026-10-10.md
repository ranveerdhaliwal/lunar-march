# LunarMarch efficiency audit, 2026-10-10

## Finding

The recorded workflows improved defect discovery but repeatedly spent more on coordination and review than the work justified. Changing the parent model alone does not address that. Treat Direct/Quick as the ordinary path and durable Task/March as evidence modes.

This audit inspected repository revision `4faebecba9152aa0af12acb4b6ccbb2acfa654da` plus existing uncommitted September evaluation records. Historical numbers below are recorded worker results, not new trials or measurements of this chat. The quote-corpus totals were independently recomputed from its 33 raw terminal records on 2026-10-10: 37,098,095 total tokens and 3,260,527 uncached input plus output, with two attempts missing telemetry. They exclude parent overhead unless the source says otherwise.

| Recorded run | Result | Overhead evidence |
|---|---|---|
| [Studio Core](studio-core-retrospective-2026-08-23.md) | Nine tasks accepted, about 87 minutes end-to-end | 28 attempts; reviews/audits consumed 62.5% of uncached input plus output |
| [Quote corpus Phase 0](live-test-results-2026-09-01-video-quote-corpus-phase0.md) | Foundation accepted | 19 attempts, five audits, 68 check executions; 1,972,852 uncached input plus output |
| [Quote corpus Phase 1](live-test-results-2026-09-01-video-quote-corpus-phase1-checkpoint.md) | Phase incomplete at the usage limit | 14 further attempts and 65 checks; whole run 33 attempts, 37,098,095 reported total tokens, 3,260,527 uncached input plus output, about 170.8 worker minutes; one of seven phases accepted |

Reviews found material defects, so eliminating all independent review would lose demonstrated value. But serial Builder/Reviewer/Fixer/Auditor passes cannot benefit from parallelism. Broad contracts mixed several acceptance boundaries and repeatedly triggered new investigations. The existing Reviewer-only cap left Builder, Fixer, and Auditor loops unbounded. Full snapshots detected unrelated concurrent edits, and repeated checks included infrastructure and pre-existing failures. Dotfile omission and stale completion state were still present in the source.

Cached tokens are not free or a published conversion to account usage. Track elapsed time, total tokens, uncached input plus output, acceptance, and missing telemetry separately. Parent work and retries must be included when comparing whole workflows.

## Comparison after the local audit

Reviewed [donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator/) at commit `f5efba0f957a1e3f0671e629ccc2c655725a7e7b` (2026-10-01). The reference ledger records exact source paths. Its project profiles pin roles and encourage bounded contracts, selective roles, and concise returns. Those are useful design ideas, not proof of cheaper execution.

Its Pro profile uses Astra medium, Luna max workers, and an Astra low reviewer. The skill mandates delegation across broad task categories, which would be too aggressive for our goal. Do not adopt blanket max effort, mandatory multi-file delegation, or its installer as a remedy.

Its [token guide](https://github.com/donvito/codex-astra-luna-orchestrator/blob/f5efba0f957a1e3f0671e629ccc2c655725a7e7b/guides/token-usage.md) reports one historical run at 13m49s with four agents and a five-hour meter change from 0% to 66%. It highlights root overhead. This is the author's sample, without local reproduction or a matched baseline; the sample used older worker settings than the current profiles. It does not establish a speed or usage advantage.

[Official multi-agent guidance](https://developers.openai.com/api/docs/guides/responses-multi-agent) likewise distinguishes independent work from ordered chains and warns that subagents can increase usage. That is conceptual support, not evidence about this desktop account's metering.

## Changes in this task

- Shortened skill entry instructions with Direct and ordinary Quick paths. Quick allows parent review when the parent did not implement the delegated change; durable acceptance retains its bound Reviewer/Auditor requirement.
- Retained current model/effort settings. The expensive part demonstrated here is the workflow; model migrations or reduced efforts require their own evidence.
- Bounded all task reservations at four by default, Reviewers at two, Auditors at two, and the run at 24. Explicit task ceilings and `init --max-attempts` are configurable before work. Failed infrastructure attempts count. Changing roles or tasks does not evade the run ceiling.
- Added status progress, remaining attempt budgets, role counts, partial token sums and missing counts. New work reactivates completed runs; legacy stale completion is corrected in displayed status.
- Preserved leading dots in source snapshots and classified already-failing invariants as baseline warnings. Passing-to-failing invariant regressions and failed acceptance commands still fail the gate.
- Focused worker packets on assigned behavior and concrete findings; reports request about 300 words and defer usage to terminal telemetry.

The installed user skill is a symlink to this repository, so repository skill edits apply to future loads without reinstalling. No external repository installer or configuration was applied.

## Validation and limits

Offline regression tests cover attempt ceilings before another reservation, cross-role and cross-task bypass, failures consuming the budget, usage missingness, truthful progress after new work, dotfile changes, and invariant baseline classification. Validation: all 46 offline tests pass; Python compilation, CLI help, the skill validator, and diff whitespace checks pass. The updated status reader was also checked against the raw quote-corpus run without editing it. One independent Luna High reviewer found setup/concurrency accounting and missing-telemetry gaps; both were corrected and re-reviewed with no material regression in the reviewed path. Exact tested source hashes are recorded in `docs/research/efficiency-validation-2026-10-10.json`.

Attempt caps are deterministic spending boundaries on launches, not hard token ceilings. One worker can still be expensive. Reservations now use an exclusive run lock, and incomplete setup directories count against budgets and missing telemetry. A process killed during reservation can leave the lock behind: status reports it, and the parent must establish that no reservation/writer can continue before removing only the stale `.reservation-lock` file. Token/time controls remain separate work. March recovery commands, finding packets, and snapshot-scoping remain future improvements. Do not claim faster or cheaper outcomes from these offline tests.

A next evaluation should compare parent-only, one Luna worker plus parent review, and durable Task on the same small bug fix and one independent two-lane task. Predeclare quality checks, model/effort/CLI versions, starting commit, and budgets; record failures as well as successes. Use small checkpoints, and include parent usage where available. Keep simultaneous unrelated account activity separate from meter attribution. No live benchmark was launched during this audit.

## Follow-up: comparison with Direct

The [multi-file CPU pilot](../evals/workflow-efficiency/results/2026-10-10-direct-v-quick.md) included the Sol parent's usage and did not meet the savings criterion. Direct took 91.615 seconds and 22,265 uncached input plus output; Quick took 102.273 seconds and 46,496, and its independent parent rejected a required CLI data-error behavior. The pilot stopped after one pair. This supports keeping tightly dependent multi-file work in the main agent and shows why worker-only measurements are insufficient. It does not establish a general model/workflow ranking. No commit or push followed the failed conditional test.

## Follow-up: removing duplicate work

Inspection of the preserved multi-file event logs found three specific causes worth fixing: the Quick parent read the implementation before dispatch, its worker loaded the coordinator skill, and the old routing guide prescribed workers/reviewers even for routine work. The disposable fixture also lacked a baseline commit, so `git diff` could not show changes to its untracked source files.

The revised routing makes Direct the default for coupled work. Quick must remove work from the parent through independent overlap, context compression, or a needed specialist/evidence boundary. A complete packet goes straight to its worker. Already assigned workers do not select modes or run orchestration. The parent reviews the resulting diff and uncovered behavior, reusing passing checks only when their file hashes still match.

For a serial workflow, the useful comparison is `dispatch + worker + review` against direct completion. A faster worker alone is insufficient; parallel speedup requires actual independent work. In the first pilot the worker alone consumed 30,668 uncached input plus output, exceeding Direct's entire 22,265. Eliminating the coordinator could not by itself reverse that result. This observation motivates reducing duplicate worker/tool activity as well as parent overhead, and declining delegation when its expected benefit is absent.

The `lean` pilot profile applies these changes with source-bound public-check evidence and a real Git baseline in both arms. It keeps the worker at `gpt-5.6-luna` high. The follow-up uses `gpt-6-astra` high for both parents at the user's request, so comparisons against the earlier Sol pilot are historical diagnostics, not isolated effects of the new instructions. The exact task and current 11-check grader remain unchanged; this is a familiar development fixture, not a new held-out benchmark. Defaults for worker model/effort and durable review are unchanged.

The [Astra follow-up](../evals/workflow-efficiency/results/2026-10-10-astra-lean.md) stopped after a false-negative CLI grade in Direct and a nested-CLI startup failure in Quick. The final launcher now dispatches the worker directly, skips review calls after failed startup, and tests actual CLI exit behavior. All 52 offline tests pass; final live efficiency remains unverified. No commit or push was made.

## Research correction: token volume versus model-weighted cost

The [community research and source ledger](../docs/research/REFERENCES.md#community-comparison-follow-up-received-2026-10-10) identifies a limitation in the earlier savings criterion. More raw tokens across different models do not necessarily mean higher credit cost. Applying current published Standard Codex rates to the existing Sol/Luna pilot yields an estimated 2.605010 credits for Direct and 2.157576 for Quick (17.176% lower), with about 80% of Quick's proxy cost in the parent. This does not measure included subscription usage or actual billed speed mode. Quick remained slower and semantically rejected; the failed benchmark and no-publish decision are unchanged. Future evaluations should retain raw telemetry but report model-weighted cost, quality, and elapsed time separately. No new worker calls were needed for this arithmetic.
