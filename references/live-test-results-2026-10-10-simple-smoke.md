# CPU-only efficiency smoke, 2026-10-10

Both paths succeeded using requested `gpt-5.6-luna`, high effort, external Codex CLI `0.162.0-alpha.17.2`. This was a tiny existing clamp-count fixture, one trial per path, with identical Builder prompts and starting files. Three model-reaching calls completed, no model retries. No GPU workloads or changes to another repository were made.

| Path | Model calls | Measured worker/launcher seconds | Total tokens | Uncached input plus output | Quality |
|---|---:|---:|---:|---:|---|
| Quick, one Builder plus parent review | 1 | 28.730 | 79,171 | 9,795 | Accepted; five public tests and property checks passed |
| Durable Task, Builder plus independent Reviewer | 2 | 48.992 | 191,626 | 21,642 | Accepted; clear gates, public/property checks passed, no review findings |

The durable Builder took 31.595 seconds and 14,965 uncached input plus output; its Reviewer took 17.397 seconds and 6,677. Variance between the two Builder calls also contributed to the difference. It is not valid to attribute the entire difference to removing a Reviewer.

Only `counter.py` changed in either project. Review did not modify the durable project. Post-worker property checks exercised 735 clamp cases, three invalid ranges, and 41 increment values. The durable run reported complete, one of one tasks accepted, two of two attempts used, and zero remaining. A third reservation was rejected with `run attempt budget exhausted (2)` before another worker call; no extra attempt directory or lingering reservation lock was created.

Quick was externally instrumented for source snapshots, usage, and checks without creating durable task state. The parent reviewed the implementation independently. Durable acceptance used its normal bound Reviewer evidence. This is not a native-versus-external transport comparison.

Preparation initially omitted `git init`, so the Quick CLI rejected its first invocation before model execution with an untrusted-directory error. That failed invocation and its missing telemetry were preserved, then both disposable projects were initialized as Git repositories. This is a smoke-harness setup defect, not a model failure. The measured successful Quick worker time excludes that 0.277-second rejection.

These measurements exclude parent/controller usage, approval-review usage, parent inspection time, and delays between calls. Another chat was active, so account-meter change was not attributed. The test verifies completion, quality checks, telemetry, independent durable review, and the run ceiling. It does not establish general speed/cost improvements or whole-workflow account savings.

Exact source and fixture hashes, all seven usage fields, command/configuration details, gates, property results, and the preserved setup failure are in [the machine-readable result](../evals/efficiency-smoke/results/2026-10-10-simple-smoke.json). Raw prompts, reports, logs, and durable evidence remain under `/tmp/lunarmarch-simple-test-20261010-ocmlrmjv`; the compact result persists in this repository even if temporary files are cleaned up.
