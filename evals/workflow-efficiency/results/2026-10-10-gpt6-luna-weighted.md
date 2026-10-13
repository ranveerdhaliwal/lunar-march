# GPT-6 Luna bounded weighted-cost pilot, 2026-10-10

**Failed the quality gate; stopped after the first pair.** The lighter workflow was faster and cheaper in this observation, but did not produce an accepted result. No repair attempt, reverse-order pair, promotion, commit or push followed.

| Workflow | Elapsed | Weighted Standard credits | Quality |
|---|---:|---:|---|
| Direct GPT-6 Astra High | 128.796 s | 15.884950 | Accepted; 19 public and 11 hidden checks passed |
| GPT-6 Luna High implementation + Astra High acceptance | 96.892 s | 8.394084 | Rejected; 13 public checks passed, 10/11 hidden checks passed |

The observed reductions were **24.8% time and 47.2% weighted cost**. This is time/cost to rejection, not successful completion. Quick used 214,102 total tokens versus Direct's 131,263; model weighting explains why its estimated cost can nevertheless be lower.

## Why it stopped

A short CSV row with a missing amount reached `Decimal(None)` and raised an uncaught `TypeError`. The CLI returned exit code 1 with a traceback instead of the required code 2. Astra's independent acceptance review caught this, and the frozen hidden test confirmed it. Astra also reported acceptance of malformed timestamp offsets such as `+01:60`; that finding was not a separate frozen hidden check. The unchanged, predeclared data-error requirement is sufficient to reject this run.

The launcher worked: one isolated Luna implementation, independently generated diff/check evidence tied to source hashes, then a fresh Astra acceptance session. No nested CLI failure or reviewer edits occurred. Luna took 47.959 s and Astra review 48.836 s; check evidence accounts for the remaining approximately 0.1 s. Weighted costs were 0.141384 for Luna and 8.252700 for Astra review. The parent review dominated cost, but removing it would have accepted a known defect.

## Protocol and evidence

The frozen plan required two counterbalanced pairs in order Direct, Quick, Quick, Direct; all quality gates; complete telemetry; and at least 10% lower mean time and weighted cost. It stopped early on any first-pair quality failure. Three model calls were used out of at most six, with 360 s parent and 180 s worker limits and no retries. All task commands used CPU only. Both arms received the same complete feature specification; no separate planning call was needed.

Preflight passed 54 offline tests, compilation, CLI help and skill validation. Grader calibration accepted the previous good Astra artifact and rejected the earlier malformed-row implementation. The frozen manifest was revalidated after the run, and per-role cost arithmetic was checked independently.

Exact configuration, source commit and hashes, frozen rates, per-role telemetry, raw trial decisions, check output, calibration, prompts and generated source are preserved in [the JSON record](2026-10-10-gpt6-luna-weighted.json). Raw CLI events remain under `/tmp/lunarmarch-gpt6-luna-weighted-20261010`. Requested CLI version: `0.162.0-alpha.17.2`; requested service tier: Standard (`default`), explicitly overridden per call. Shared global configuration and GPU work were untouched.

Cost uses uncached input, cached input and output at the frozen [official Standard credit rates](https://learn.chatgpt.com/docs/pricing), with reasoning already included in output. It is a normalized estimate, not an invoice or subscription-meter measurement; requested tier is not independent proof of served tier. Elapsed time covers model startup, implementation, evidence collection and acceptance, excluding evaluator/setup/controller and external approval review. Separate fresh CLI sessions approximate direct versus delegated work, rather than replaying this accumulated chat. This is a familiar development fixture and one failed pair, so it does not establish a general ranking or justify changing worker defaults.

## Decision

Keep the improvement experimental. The result now points to worker error-path coverage rather than launch overhead as the immediate blocker. A future separately authorized experiment could make concrete malformed-input examples part of the contract for both arms, or allow one bounded repair whose time and cost count toward the workflow. Neither was tried here; modifying this frozen run to rescue the result would invalidate the comparison.
