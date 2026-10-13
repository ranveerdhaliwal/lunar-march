# LunarMarch

LunarMarch supports bounded Luna/OpenCode delegation and optional durable evidence for risky or resumable work. Ordinary tasks stay in the parent or use one worker with parent review. Durable Builder/Reviewer loops and phase Auditors are reserved for work that needs them.

The [efficiency audit](references/efficiency-audit-2026-10-10.md) explains earlier overhead. **Direct remains the default: no completed comparison has demonstrated accepted results with both lower elapsed time and weighted cost.** GPT-6 Luna sometimes reduced cost, but quality failures or review time prevented a win on both measures. The installed skill was disabled locally on 2026-10-10 and remains disabled; this repository retains its implementation for explicit experiments.

See [current benchmark findings and reproduction](references/workflow-benchmarks.md). Durable runs now enforce attempt caps; experimental launchers reuse source-bound checks, stop immediately on failed quality or missing usage, and offer isolated per-call state for concurrent tests. These controls are offline-tested; they are not a claim of measured performance gains.

```text
parent authority
  ├─ Scout fan-out (read-only research)
  ├─ Builder → Reviewer → Fixer loop
  ├─ Sentinel (long waits and monitoring)
  └─ phase barrier → Auditor → parent acceptance
                         │
                  objective integrity gate
```

GPT-5.6 Luna remains the in-house default. The same durable core can now launch DeepSeek and other provider models through OpenCode. The parent model keeps decomposition, ambiguity resolution, risk decisions, and final acceptance; deterministic helpers bind contracts and prove lifecycle, hashes, source movement, declared write scope, and acceptance-command results regardless of transport.

## Why another orchestrator?

Existing projects each solve a valuable portion of the problem. LunarMarch combines their strongest general ideas into a small transport-neutral core with first-class Codex integration:

- immutable attempts and objective gates for trustworthy long runs;
- risk-aware Luna routing and independent reviews;
- scalable read-only fan-out with bounded concurrency;
- explicit lifecycle, retry budgets, recovery, and phase barriers;
- one contract format shared by research and implementation.

See [references/influences.md](references/influences.md) for the projects studied and the design boundary.

## Current status

Version `0.2.0` includes the skill, contract schema, Codex and OpenCode worker transports, durable run state, scope snapshots, integrity gates, checkpointed evaluations, recovery-safe status, examples, and offline tests. The first model-backed Task evaluation completed successfully on 2026-08-22; a one-call Luna smoke also succeeded on 2026-08-23. A real two-phase Studio Core run accepted nine tasks, exposed review-heavy marginal usage, and drove the latest transport and contract improvements. See [the Studio Core results](references/live-test-results-2026-08-23-studio-core.md) and [improvement plan](references/studio-core-retrospective-2026-08-23.md). Historical verification is in [references/testing-and-evaluation.md](references/testing-and-evaluation.md); the latest workflow experiments and checks are summarized in [the benchmark guide](references/workflow-benchmarks.md).

## Choose a workflow

| Work shape | Starting path |
|---|---|
| Small or tightly dependent edits, even across several files | Direct in the main agent |
| Independent work that can overlap, substantial context to compress, or a required specialist boundary | Quick: one worker and parent review |
| Required immutable evidence or recovery | Durable Task |
| Meaningful phase boundaries and cross-task risk | March |

The [tiny smoke](references/live-test-results-2026-10-10-simple-smoke.md) verified operation and attempt limits but excluded parent usage. The [multi-file pilot](evals/workflow-efficiency/results/2026-10-10-direct-v-quick.md) included parent coordination: Direct took 91.615 seconds and 22,265 uncached input plus output; Quick took 102.273 seconds and 46,496. It stopped after one pair under its predeclared rule. This is fixture-specific evidence, not a general model ranking or an account-meter conversion. Do not delegate merely because a change touches several files.

## Durable quick start

```bash
python3 scripts/lunarmarch.py init \
  --project-root /absolute/project \
  --run-root /absolute/project-run \
  --goal "Add cursor pagination" \
  --mode task

python3 scripts/lunarmarch.py add-task \
  --run-root /absolute/project-run \
  --spec examples/task-contract.json

python3 scripts/lunarmarch.py launch \
  --run-root /absolute/project-run \
  --task-id users-pagination \
  --role builder \
  --run-checks
```

The default path requires an installed, authenticated Codex CLI with access to `gpt-5.6-luna`. Run `python3 -m unittest discover -s tests -v` for offline verification. CI repeats compilation, the command-interface smoke check, and the full offline suite on Python 3.11-3.13.

To use DeepSeek through OpenCode instead:

```bash
python3 scripts/lunarmarch.py launch \
  --run-root /absolute/project-run \
  --task-id users-pagination \
  --role builder \
  --transport opencode \
  --model deepseek/deepseek-v4-flash \
  --run-checks
```

OpenCode stores the DeepSeek credential; LunarMarch never reads or records the API key. LunarMarch workers require that saved OpenCode credential because their child environment excludes API keys. See [references/providers.md](references/providers.md) for setup, the Sol-orchestrator/DeepSeek-worker design, permission differences, and how to add another transport.

The OpenCode adapter is covered by fake-CLI integration and permission-policy tests. No paid DeepSeek call was made in this repository yet; the first authenticated smoke test remains pending until a key and OpenCode installation are available.

DeepSeek can also be configured directly as a Codex model using DeepSeek's official Codex integration. After that one-time local setup, pass `--transport codex --model deepseek-v4-flash` to LunarMarch. This is useful for a native Codex smoke test, while the OpenCode transport remains the better default for provider-neutral worker routing. The direct setup changes global `~/.codex` configuration, so review it and preserve the generated backup before switching back to Luna.

The model-backed procedure is documented in [references/live-test.md](references/live-test.md). It uses a disposable intentionally-failing fixture, a Luna Builder, a fresh Luna Reviewer, objective gates, and explicit parent acceptance.

## Measured context policy

Native workers default to no inherited conversation plus a compact resolved contract and exact workspace paths. A bundled evaluator measures whether that saves usage without degrading task quality. It uses opaque trial identities, counterbalanced order, deterministic hidden graders, authoritative terminal usage telemetry, and completeness checks. In the first clean six-pair case study, compact context used 17.9% fewer cumulative tokens; all code-behavior checks passed, but one compact worker created an undeclared report file, producing mean overall quality of 98.33 versus 100. See [the result](evals/context-efficiency/results/2026-08-22-contract-v-padding.md) and [the evaluation protocol](references/context-evaluation.md). New direct Codex worker runs also persist token fields in their terminal records. Use `not reported` when a provider does not expose usage.

### What the evidence currently says

| Question | Current evidence |
|---|---|
| Does compact resolved context save usage? | Yes on the bundled fixture: 17.9% fewer total tokens and 30.0% fewer uncached input tokens. |
| Did compact context produce incorrect code? | No. All hidden behavior, public tests, and compilation checks passed in all 12 trials. |
| Was overall execution quality identical? | No. One compact trial created an undeclared report file, so mean overall quality was 98.33 versus 100. |
| Is compact context proven universally better? | No. This is a clean but exploratory single-fixture result. |
| Why keep compact as the default? | It met the predeclared two-point quality tolerance while materially reducing usage; LunarMarch still requires complete task contracts and objective review. |

### Verification performed

- 34 orchestration and transport tests cover immutable contracts, attempt lifecycle, write boundaries, acceptance evidence, protected invariants, review budgets, independent review, phase freezing, Codex/OpenCode launch policies, environment isolation, bounded timeouts, recovery safety, and installation behavior.
- 12 evaluator tests cover opaque trial identities, balanced ordering, packet equivalence, terminal usage parsing, malformed grader handling, missing-trial and missing-telemetry rejection, sealed checkpoint/resume, tamper rejection, end-to-end scoring, and source-repository isolation.
- 22 workflow/runtime tests cover weighted multi-model accounting, immediate failure stops, source-bound checks, semantic acceptance, overlapping workers, scoped merges, reviewer mutation rejection, private credentials and cleanup. Together with the 46 tests above, all 68 passed on 2026-10-12.
- A CPU-only multi-file pilot compared Direct against Quick with parent usage included and stopped without meeting the savings criterion.
- One live Task evaluation exercised Builder, Reviewer, objective gates, retry recording, and parent acceptance.
- One blinded context evaluation ran 12 Luna workers in six matched pairs from a clean commit.
- An independent Luna audit found eight evaluator defects and one order-balance defect; all were corrected and covered by regression tests before the published run.

For historical test coverage, read [references/testing-and-evaluation.md](references/testing-and-evaluation.md). The [2026-10-12 validation record](docs/research/efficiency-validation-2026-10-12.json) identifies the latest checked source hashes.

### Expanding to 3-5 additional fixtures

A credible next set should cover research synthesis, multi-file implementation, diagnosis from incomplete evidence, resumable multi-phase work, and reviewer/fixer recovery. It no longer needs to happen in one expensive session: create the full immutable manifest once, run one or two trials with `--max-new-trials`, then continue later with `--resume`. A useful cadence is one fixture design session followed by six two-trial checkpoints. Partial checkpoints are preserved but cannot support a quality claim until the balanced roster is complete. See [references/testing-and-evaluation.md](references/testing-and-evaluation.md#bite-sized-execution-plan).

### CPU-only workflow pilot

The launchers freeze fixtures, briefs, graders and source hashes, include worker and review costs, and stop after any quality or telemetry failure. The first pair must meet the time and cost thresholds before a reverse-order pair is permitted. Two complete pairs are required for the experiment's success gate. Raw logs stay outside the repository; compact evidence is retained here.

For an explicit two-worker test while other chats are active, use per-call isolation:

```bash
python3 scripts/parallel_eval.py prepare --output /tmp/lunarmarch-parallel-new --isolated-runtime --parallel-first --pairs 1
python3 scripts/parallel_eval.py run-one --output /tmp/lunarmarch-parallel-new
python3 scripts/parallel_eval.py summarize --output /tmp/lunarmarch-parallel-new
```

Preparation and summarization make no model calls. Each `run-one` consumes usage; after a failed trial it returns the stop decision without launching more models. A one-pair diagnostic cannot meet the two-pair success gate. Isolation changes only child runtime state, leaving shared configuration and daemons alone; model usage still counts against the same account. See [the protocol and limitations](references/workflow-benchmarks.md) before spending on another comparison.

The concrete fixture contracts, graders, success evidence, and stop conditions are written out in [references/fixture-roadmap.md](references/fixture-roadmap.md).

### Writing results from another chat

After a Sol, Luna, DeepSeek, or other worker run, record the result in [the metrics report template](references/metrics-report-template.md). Use `references/live-test-results-YYYY-MM-DD.md` for one bounded run, or `evals/<series>/results/` for repeated comparisons. Include model, transport, effort or variant, attempts, gate or quality result, and token fields. Use `not reported` when the provider does not expose usage.

## Installation as a skill

The local installation used for these experiments remains disabled pending a convincing workflow result. The following commands are for deliberate installation, not a step required to run offline tests.

For every local Codex or OpenCode chat:

```bash
python3 scripts/install_skill.py --scope user
```

For chats working inside one repository:

```bash
python3 scripts/install_skill.py --scope repo --repo-root /absolute/project
```

See [references/installation.md](references/installation.md) for discovery behavior, safe replacement, explicit invocation, and future plugin distribution.

### Avoid repeated orchestration

A fully specified assignment does not need a coordinator model to reread its inputs and launch a fixed command. Use native dispatch in the current chat; for scripted fixed work, let the launcher dispatch and collect the diff/check evidence, then ask the parent to review uncovered behavior. Already assigned workers execute their packet without loading coordinator references. Reuse unchanged checks instead of repeating the implementation pass.

The [Astra follow-up](evals/workflow-efficiency/results/2026-10-10-astra-lean.md) identified a nested-CLI startup failure and an overly restrictive grader. It did not establish savings. The follow-up stopped without retries or publishing, and led to the deterministic dispatch and CLI-grading fixes above. Coupled tasks still default to Direct; the external Astra/Luna example is not installed, and the Luna model/effort defaults remain unchanged.

## Safety model

LunarMarch does not grant authority. Read-only roles use a read-only sandbox; write roles require declared owned paths; destructive and external actions remain subject to the parent and user’s normal authorization boundary. Mechanical PASS never means the engineering is accepted.

## Contributing

Contributions are welcome, especially small deterministic fixtures, transport adapters, permission hardening, and independent reproductions. Contributors do not need to fund a full live benchmark: fixture design, hidden graders, fake-CLI tests, and leakage audits are useful standalone pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
