# Stronger error examples: GPT-6 Luna versus Direct Astra, 2026-10-10

**Stopped after the first pair because Quick failed independent acceptance.** Concrete examples fixed the previous defects, but did not generalize to malformed offset variants. No retries, reverse-order pair, default promotion, commit or push followed.

| Workflow | Elapsed | Weighted Standard credits | Frozen grader | Acceptance |
|---|---:|---:|---|---|
| Direct GPT-6 Astra High | 136.018 s | 16.081400 | 11/11 passed | Accepted |
| GPT-6 Luna High + Astra High review | 104.022 s | 8.3373115 | 11/11 passed | Rejected |

Observed reductions: **23.5% time and 48.2% weighted cost**. These measure time/cost to rejection, not successful Quick completion. Public tests passed (19 Direct, 11 Quick), as did compilation, scope and reviewer immutability gates. Three model calls used; all local work was CPU-only.

## What changed and what failed

The same shared task brief, passed to both implementations and Quick review, now gives concrete missing/empty/invalid amount cases, invalid timezone offsets, bounds errors, and invalid event timestamps outside a window. The grader was strengthened before freezing to check malformed offset minutes and all three amount cases, including no traceback. Harness, fixture, model effort and pricing assumptions remain as in the prior weighted pilot.

Luna now correctly handles the previous missing-amount and `+01:60` failures. Its parser still accepts `+01:60:00` and `+01:59:60`, silently normalizing them. Astra review found that malformed event timestamps and CLI bounds return exit 0 with JSON instead of exit 2 with empty stdout. Passing example tests was therefore insufficient under the original general requirement to reject malformed timestamps.

The controlling agent independently ran identical probes against both outputs without changing their source. Direct rejected both variants through the parser and actual CLI; Quick accepted both. These post-hoc probes confirm the review finding and were not silently added to frozen scores.

Preflight also found that the previous Direct artifact accepted `+01:60`, which its original grader had missed. That historical result remains preserved, with this limitation recorded. A corrected disposable calibration copy passed the strengthened grader; neither benchmark model saw the correction.

## Bounds, evidence and interpretation

The predeclared plan required Direct/Quick/Quick/Direct, at most six calls, no retries, parent/worker limits of 360/180 seconds, all quality gates, complete telemetry, and at least 10% lower mean time and cost. First-pair failure stops the run. Two of four planned trials ran, so no balanced performance claim is supported.

All 54 offline harness tests passed. The frozen manifest was revalidated after both trials and cost arithmetic checked against per-role telemetry. Exact source/brief/grader/runner hashes, configuration, calibration, trial records, generated source, prompts and symmetric probes are in [the JSON record](2026-10-10-gpt6-luna-error-examples.json). Raw CLI logs remain at `/tmp/lunarmarch-gpt6-luna-errors-20261010`. No global configuration or GPU work changed.

Weighted cost uses the frozen [official Standard credit rates](https://learn.chatgpt.com/docs/pricing) for actual uncached input, cached input and output. It is not an invoice or included subscription usage. Standard tier was explicitly requested; served model/tier was not independently attested. Timings include implementation, source-bound evidence and acceptance, but exclude setup/controller, external approval review and post-run grading/probes. Fresh separate CLI sessions proxy direct versus delegated work. This is a familiar development fixture, not held-out evidence of general savings.

## Decision

Keep the candidate experimental. More examples helped, but Luna's validation remained narrower than the stated input rule. The next hypothesis would be an explicit accepted timestamp grammar and tests spanning that grammar, rather than an expanding list of individual bad strings. A bounded repair is another untested option and would need its entire time/cost counted. Neither is part of this completed run.
