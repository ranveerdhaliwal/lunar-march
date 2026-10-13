# Executable-contract API migration pilot, 2026-10-10

**Both arms passed; Quick cost less but took longer.** The first pair failed the predeclared requirement to save at least 10% in both time and weighted cost, so the run stopped. No retries, reverse-order pair, promotion, commit or push. The installed LunarMarch skill remains disabled.

| Workflow | Elapsed | Weighted Standard credits | Quality |
|---|---:|---:|---|
| Direct GPT-6 Astra High | 43.959 s | 8.372750 | Accepted |
| GPT-6 Luna High + Astra High review | 48.298 s | 6.548998 | Accepted |

Quick was **21.8% cheaper and 9.9% slower**. Each arm passed four legacy tests, eight protected executable acceptance tests, two independent post-run probes, compilation, exact write-scope and semantic acceptance. All local work used CPU only.

## Tested change

Both implementations received the same five-file API migration task and protected acceptance tests before editing. The task renames the canonical reporting function while keeping a dynamic compatibility wrapper, migrates CLI and service callers, exports both APIs and updates documentation. Existing Decimal, sorting, empty-input and CLI behavior must remain intact. The parent reviews the actual diff and source-bound test evidence, adding probes only for concrete gaps in the contract. It did not rerun recorded passing tests or mutate the worker output.

Luna took 24.519 seconds; Astra acceptance took 23.582 seconds; evidence collection accounts for about 0.2 seconds. Estimated role costs were 0.060698 credits for Luna and 6.488300 for Astra review. Review accounts for 99.1% of Quick's weighted cost and almost half its elapsed time. The remaining delay here is the serial implementation-plus-review path, not a correctness repair loop.

This does not prove that tests alone caused the improvement: the task family and review focus also changed. The acceptance checks were authored as benchmark setup. Their authoring time and this controlling chat's usage were not measured in the two arms. The result describes implementation when acceptance already exists, not full one-off task savings from scratch.

## Bounds and evidence

Plan: Direct/Quick/Quick/Direct, at most six calls, 360/180 second parent/worker limits, no repairs or replacement trials. Success required all quality gates, complete telemetry, two pairs, and Quick mean time and weighted cost each at most 90% of Direct. First-pair failure stops the run. Three calls completed in two of four planned trials.

Preflight: 55 harness tests, compilation and diff checks passed. Calibration accepted a correct migration and rejected the unmigrated fixture, static compatibility alias and unmigrated service. The runner supports case-specific protected checks and exact owned paths; the original fixture defaults remain supported. Manifest hashes were revalidated after execution and weighted costs recomputed from per-role telemetry.

Exact configuration, fixture/task/runner/grader hashes, calibration and generated source are preserved in [the JSON record](2026-10-10-api-migration.json). Raw CLI logs are at `/tmp/lunarmarch-api-migration-20261010`. Current task source: [API migration](../../api-migration/task.md).

Cost uses the frozen [official Standard credit snapshot](https://learn.chatgpt.com/docs/pricing) for uncached input, cached input and output, without double-counting reasoning. Both models requested High effort and Standard tier. This is a normalized credit proxy, not an invoice or included subscription-meter result, and served identities were not independently attested. Fresh CLI sessions proxy direct versus delegated work. Setup/controller, external approval-review and post-run grading costs are excluded.

## Disablement and decision

Removed only the installed symlink `/home/ranveer/.agents/skills/lunar-march`, which pointed to this repository. No matching auto-trigger instruction was found in checked user/home AGENTS.md and Codex rule files. Historical project trust records remain. The repository and GPU work are intact. Restoration is documented in [the disablement record](../../../docs/research/2026-10-10-skill-disabled.json). Existing chats may retain previously loaded skill text; it is no longer discoverable through the installed link.

Keep small coupled migrations Direct when both speed and cost matter. This run supports a possible cost/latency tradeoff when executable acceptance exists, not a faster default. Actual independent work that can overlap is a future candidate; it was not tested here. Do not automatically re-enable the skill based on this one correct but slower pair.
