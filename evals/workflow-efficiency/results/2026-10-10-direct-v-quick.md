# Direct versus Quick multi-file pilot, 2026-10-10

## Decision

Quick did not save measured time or tokens on this task, and its parent rejected a required CLI error behavior. Stop after the first pair. The user authorized commit/push conditional on success, so no commit or push was performed.

| Workflow | Model-reaching calls | Elapsed seconds | Total tokens | Uncached input + output | Parent decision |
|---|---:|---:|---:|---:|---|
| Direct Sol High | 1 | 91.615 | 129,529 | 22,265 | accepted |
| Quick Sol High coordinator + Luna High worker | 2 | 102.273 | 445,088 | 46,496 | rejected |

Requested models: `gpt-6.1-sol` for both parents, `gpt-5.6-luna` for the Quick worker; high effort throughout, external Codex CLI `0.162.0-alpha.17.2`. The parent model/effort match the current chat's recorded settings. Requested identity is launch configuration evidence, not independent proof of provider runtime identity.

Quick took 11.6% longer, used 2.09 times the uncached input plus output, and 3.44 times total tokens. Luna's implementation alone took 54.604 seconds and 30,668 uncached input plus output. Its Sol coordinator used another 15,828. The coordinator's wall time includes waiting for the child, so child time is not added twice.

## Task and controls

The task added optional UTC time-window filtering to a small CSV reporter across parsing, aggregation and CLI modules, plus a test file. Both workflows began with identical files, task requirements, ownership and four passing legacy tests. Both changed only the three owned modules and `tests/test_windows.py`; protected files stayed unchanged. All code, tests and compilation were CPU-only. No packages were installed or GPU/other-repository work performed.

Direct implemented and checked the feature in a fresh main-agent session with no delegation. Quick dispatched exactly one compact Luna worker, then its Sol parent inspected the implementation and checked it. No repairs or model retries were permitted. This measures fresh external-CLI workflow proxies, not the literal accumulated history of the current desktop chat or a native-subagent transport comparison.

The plan allowed two pairs in opposite order (Direct/Quick, then Quick/Direct), six model-reaching calls maximum. Each root was capped at 360 seconds and each worker at 180 seconds. Success required passing behavior/scope, complete primary telemetry, and at least 10% lower Quick mean elapsed time, total tokens and uncached input plus output. The predeclared early-stop rule ended the pilot after the first pair failed thresholds. No replacement or reverse-order trials ran.

## Quality and grading gap

Direct passed 20 public tests and the ten predeclared post-run checks. Quick passed 11 public tests and those same ten checks. However, Quick's independent parent explicitly declined acceptance: a short CSV row with a missing amount produced a traceback and exit code 1, while the task required data errors to return 2 with stderr and no JSON stdout.

A separate post-hoc probe reproduced this: the untouched baseline and Quick returned 1; Direct returned 2. The defect was inherited from the fixture, but Direct satisfied the new task's data-error requirement and Quick did not. This probe is additional evidence, not a secretly added predeclared grader.

The first evaluator's `quality_pass` field captured mechanical checks only. It therefore said true even for the parent-rejected Quick result. Original trial fields are preserved in the result JSON with explicit semantic adjudication, rather than silently rewritten. The current harness now requests a structured parent acceptance decision and includes the malformed-row check. No new live calls were made with those hardened versions.

## Interpretation and reproducibility

This is an early-stopped exploratory pilot on one task. It supports Direct for this tightly dependent change; it does not show that Quick always loses, or decide whether independent research/implementation lanes help. It is not a six-pair publishable performance study and does not promote a model/effort change.

Root plus child provider-reported usage is included, with all seven token fields retained. Benchmark construction, this controlling chat, and external automatic-approval reviewer usage are excluded. Another chat was active; neither account-meter usage nor pricing is inferred from these token counts.

The tested fixture, task, grader, runner and skill are bound by hashes. The suite was uncommitted (`dirty_suite_override: true`), so this remains a pilot report rather than a clean-commit general claim. Exact per-model usage, checks, source hashes, preserved root decisions, manifest and post-hoc probes are in [the result JSON](2026-10-10-direct-v-quick.json). Raw evidence and the frozen v1 runner/grader remain at `/tmp/lunarmarch-workflow-pilot-20261010-final`. The current harness hashes differ because it was hardened after discovering the grading gap.

## Final offline validation

All 50 repository tests passed after the harness hardening. Compilation, the skill validator and whitespace checks passed. The hardened post-hoc grader passed 11/11 on Direct and 10/11 on Quick, reproducing the parent's rejection. A full Linux filesystem interrupted one verification run; a Windows-temp rerun exposed an existing timing-test sensitivity to slow mounted storage. The focused timing check and final full suite passed with Linux temporary files once space was available. Exact current source hashes and environment notes are retained in the result JSON.
