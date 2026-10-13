# Two parallel Luna workers versus Direct Astra, 2026-10-10

**The parallel comparison stopped on a launcher failure. No speed or total-cost conclusion is supported.** Direct completed correctly; only one of the two Luna workers completed, so integration and Astra review were skipped. The installed LunarMarch skill remains disabled. No retries, reverse-order pair, commit or push.

| Workflow | Measured elapsed | Weighted Standard credits | Result |
|---|---:|---:|---|
| Direct GPT-6 Astra High | 202.107 s | 22.610200 | Accepted |
| Two GPT-6 Luna High launch attempts | 47.011 s | Unknown | CSV startup failed; JSONL completed; no review |

The second duration is time to failure, not completion. It cannot be reported as a speedup. CSV telemetry is missing, so neither total tokens nor total cost may be replaced with zero or a partial sum.

## Task and execution

The larger fixture adds JSON Lines and CSV import/export to an existing conversion CLI. Each lane owns its formatter, tests and documentation in an independent checkout, with shared protected record/schema helpers, CLI and supplied acceptance tests. The launcher starts both workers concurrently, checks their exact write boundaries and local tests, merges only their disjoint owned files, runs combined checks, and invokes one Astra acceptance review. Full parallel timing starts before worker checkout/dispatch and includes merge, verification and review when reached. Cost sums actual per-model telemetry across both workers and reviewer, including failed attempts when available.

Direct passed 23 unit tests, 16 protected acceptance tests, three independent probes, compilation, exact scope and semantic acceptance. The JSONL worker finished in 46.865 seconds, passed 10 local unit tests and seven lane acceptance tests, and stayed inside its three owned paths. Its known cost proxy is 0.1682315 credits, which is only a partial component of the failed workflow.

The CSV worker exited after 0.493 seconds without model usage telemetry:

```text
Error: thread/start: thread/start failed: failed to load configuration: Failed to read config file /mnt/c/Users/ranve/.codex/config.toml: No data available (os error 61) (code -32600)
```

Its launch began about one millisecond after JSONL. This establishes concurrent launch attempts, not successful overlap of two model workloads. A shared-config read failure during startup suggests a launcher/configuration issue worth investigating; it does not prove a write race or service/model defect. No shared config was repaired or changed in response. JSONL's completed result and telemetry were retained, and no review call was purchased for an incomplete implementation.

## Bounds and evidence

The frozen protocol specified Direct/parallel/parallel/Direct, at most eight model calls, no repairs/replacement trials, 180 seconds per worker, 240 seconds Direct and 120 seconds review. First-pair quality, telemetry or efficiency failure stops the run. Success required two complete pairs, all quality gates and at least 10% lower mean time and cost. Three launches occurred: Direct, JSONL and failed CSV; two produced completed model results. No Astra review or second pair ran.

Preflight passed 60 offline tests, including synchronized concurrent dispatch, retaining the other worker's usage after failure, protected-scope merging, three-role accounting and rejecting reviewer edits. Calibration accepts a known-good implementation and rejects unimplemented stubs, non-atomic JSONL writes and lost CSV tags. Those implementations were not supplied to models. Frozen fixture/task/grader and four runner dependency hashes were revalidated after the failure.

Exact model/configuration/source hashes, per-role telemetry, failure text, calibration, prompts and generated artifacts are in [the JSON record](2026-10-10-parallel-exporters.json). Raw logs remain at `/tmp/lunarmarch-parallel-exporters-20261010`. Both models requested High effort and Standard tier. The [official pricing snapshot](https://learn.chatgpt.com/docs/pricing) is a normalized credit proxy, not an invoice or account-meter measure; served model/tier was not independently attested. Setup, acceptance authoring, this controller, external approval review and post-run grading are excluded. All local task work was CPU-only and GPU work was untouched.

## Decision

Keep the skill disabled and preserve this as a failed infrastructure trial. Before another paid comparison, establish a reliable way to start concurrent CLI sessions without depending on a failing shared configuration read, then freeze a fresh bounded run. A per-run configuration/state isolation approach is a candidate, not an implemented or verified fix. Do not resume or relabel this failed trial as a successful comparison.
