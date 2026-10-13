# Workflow benchmark status, 2026-10-12

Direct remains the default. No completed experiment has met quality acceptance plus at least 10% lower mean time and weighted cost across two pairs. The installed LunarMarch skill remains disabled. Committing the experimental tooling and evidence does not enable it or promote a workflow.

## Findings

| Experiment | Direct | Delegated, including review | Decision |
|---|---|---|---|
| [GPT-6 Luna](../evals/workflow-efficiency/results/2026-10-10-gpt6-luna-weighted.md) | 128.796 s / 15.884950 credits | 96.892 s / 8.394084 credits | Rejected for missing CSV amount behavior |
| [Stronger examples](../evals/workflow-efficiency/results/2026-10-10-gpt6-luna-error-examples.md) | 136.018 s / 16.081400 credits | 104.022 s / 8.3373115 credits | Rejected for malformed timestamp offsets |
| [API migration](../evals/workflow-efficiency/results/2026-10-10-api-migration.md) | 43.959 s / 8.372750 credits | 48.298 s / 6.548998 credits | Both accepted; lower cost but slower |
| [Two parallel workers](../evals/workflow-efficiency/results/2026-10-10-parallel-exporters.md) | 202.107 s / 22.610200 credits | Startup failure; complete cost unknown | No valid efficiency comparison |
| [Isolated parallel runtime](../evals/workflow-efficiency/results/2026-10-10-isolated-runtime.md) | Not launched after rejection | 145.589 s / 10.0693015 credits | Startup fix worked; required row diagnostic failed |

Credits use the frozen 2026-10-10 Standard pricing snapshot, with uncached input, cached input and output priced separately for each model. Reasoning is already included in output. These are normalized cost estimates, not account quota or invoice measurements. Rejected trials report time and cost to rejection, not accepted completion. Raw token totals alone do not compare differently priced models fairly.

Astra review accounted for 9.752350 of the isolated trial's 10.0693015 credits and 45.237 seconds. Improving worker cost alone cannot remove this review expense. Supplied executable contracts and focused review remain candidates; their setup/controller cost was excluded from the experiments and must be included in any claim about a one-off task's total cost. Historical fresh CLI sessions also do not reproduce an already-running main chat's cache and context.

## Further improvements, 2026-10-12

- Both launchers now stop immediately after any trial fails quality or complete usage accounting, including the first parallel trial or the third trial in a reverse-order pair. A failed first pair's efficiency threshold also stops continuation. No repair/replacement trial is bought automatically.
- Acceptance decisions must identify the task requirement and concrete evidence behind a rejection. Optional suggestions cannot silently expand the task; stated requirements still apply even when public checks pass.
- The CSV integer-limit diagnostic discovered by review is now an upfront protected acceptance check and appears in the common brief supplied to both arms. This changes future fixtures only. Disposable-copy calibration passes the historical Direct implementation and rejects the parallel implementation on precisely this error; original scores and frozen files are unchanged.
- Isolated authentication rejects malformed, non-finite or unsupported session metadata locally. Shared auth/config files are read-only inputs; no refresh credential is copied. Each test call's private state is removed on normal completion or handled failure.

Validation: 68 offline tests passed, including both launchers refusing further invocation after a first-trial failure. The eight-check CSV calibration is recorded with source hashes in [the calibration JSON](../docs/research/2026-10-12-regression-calibration.json). No additional model calls or GPU work were performed for these changes. Their performance effect is unmeasured.

## Bounded reproduction

For a new isolated diagnostic, from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/parallel_eval.py prepare --output /tmp/lunarmarch-parallel-new --isolated-runtime --parallel-first --pairs 1
python3 scripts/parallel_eval.py run-one --output /tmp/lunarmarch-parallel-new
python3 scripts/parallel_eval.py summarize --output /tmp/lunarmarch-parallel-new
```

Use a fresh output directory. Preparation is offline apart from reading the local CLI version. Each `run-one` may launch models and spend usage: two parallel GPT-6 Luna High workers and then one GPT-6 Astra High review, or one Direct Astra call. A one-pair plan permits at most four calls, with 180 seconds per worker, 120 seconds review and 240 seconds Direct. Run the second arm only if the first passes. Completed one-pair results cannot establish the two-pair success gate. For a predeclared full comparison, prepare with `--pairs 2`; never extend or overwrite a finished frozen plan.

`--isolated-runtime` is opt-in. It uses child-only CODEX_HOME/CODEX_SQLITE_HOME, `--no-daemon` and `--ignore-user-config`, without changing shared settings or interrupting other chats. Manual stripped-session compatibility was tested with CLI 0.162.0-alpha.17.2; it is not guaranteed across CLI versions. Insufficient token lifetime fails locally without refreshing shared login. Calls still share account usage limits. Private state lives under ignored `.lunarmarch/isolated-runtime`; abrupt host termination can prevent cleanup, so keep that directory out of commits.

The isolated comparison includes authentication setup/cleanup, dispatch, merge, combined checks and review in elapsed time, and sums all roles' available usage. Missing usage is unknown, never zero. Setup/test-authoring/controller, external approval review and post-run hidden grading are excluded. Worker invocation intervals overlap; do not sum their seconds as parallel wall time.

Historical reports and their frozen hashes remain unchanged. The [reference ledger](../docs/research/REFERENCES.md) distinguishes external suggestions from local measurements and records adoption decisions. The user's 2026-10-12 request authorizes committing this work despite the absence of a performance winner; earlier reports' “no commit/push” decisions describe those historical turns.
