# Astra follow-up, 2026-10-10

The follow-up found actionable workflow and evaluator defects, but did not complete a valid efficiency comparison. No retries, reverse-order pair, commit, or push followed the failed first pair.

| Arm | Elapsed | Reported uncached input + output | Outcome |
|---|---:|---:|---|
| Direct Astra High | 69.736 s | 31,902 | 18 public tests passed; correct CLI behavior; frozen grader produced one false negative |
| Astra coordinator + Luna High attempt | 30.489 s | Parent 7,136; worker not reported | Worker startup failed; parent correctly rejected |

The second duration measures failure, not faster completion. Requested identities were `gpt-6-astra` high and `gpt-5.6-luna` high via Codex CLI `0.162.0-alpha.17.2`. Two parent calls completed; the one worker launch failed in 0.200 seconds with read-only filesystem/database errors before producing a model result. Root-plus-worker token totals remain unknown, not zero. Everything was CPU-only in disposable fixtures.

## What changed and what the test revealed

The tested candidate dispatched a complete assignment without parent reconnaissance, told workers to avoid coordinator skills, used real Git baselines, and supplied independently collected diff/check evidence tied to file hashes. It retained the same task and 11 frozen checks. This is a familiar development fixture, not a held-out benchmark. The parent model changed from the earlier Sol pilot, so cross-run differences cannot isolate the instruction changes.

Direct's apparent failure was a grader error. The contract required CLI exit code 2, but the grader called `main()` directly and rejected argparse's valid `SystemExit(2)`. Actual module invocations returned 2, useful stderr and no stdout. The corrected post-hoc grader passes all 11 checks on Direct and still rejects the earlier Luna malformed-row defect. Frozen results remain unchanged.

Quick's worker launch failed because the nested CLI inherited a sandbox where its local state was read-only. The parent stopped without repairing or retrying. This provides no evidence for or against the candidate's successful completion speed.

## Final local improvements

- Resolved routing contradictions: coupled work stays Direct; delegation must remove meaningful parent work or satisfy a needed specialist/evidence boundary.
- Already assigned workers execute their packet rather than running orchestration.
- The default scripted `lean` profile now starts the worker directly from the launcher, then invokes the independent parent for acceptance. It skips that model call after failed worker startup. Interactive chats should use native dispatch where available.
- Review uses a real diff and source-bound check evidence. Reviewer mutations invalidate acceptance; uncovered behavior still needs review or a targeted probe.
- CLI grading now exercises the actual command-line interface. Disposable baseline commits contain source snapshot files, excluding generated caches.

These final launcher changes happened after the live trial and have **offline validation only**. All 52 repository tests, compilation, skill validation and whitespace checks pass. The tests cover worker-before-review ordering, skipping review after failure, missing usage, source evidence and rejecting reviewer edits. No worker model/effort or global configuration was changed.

Exact frozen and current hashes, raw trial records, post-hoc grading and limitations are in [the result JSON](2026-10-10-astra-lean.json). Raw logs remain at `/tmp/lunarmarch-astra-lean-20261010`. Benchmark construction, this controlling chat and external approval-review usage are excluded. Token counts do not establish account-meter savings or monetary cost. The next live check, if pursued, must use a fresh frozen plan for the final launcher; do not resume or relabel this failed pair.
