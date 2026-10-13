Add optional UTC time-window filtering to this CSV activity reporting tool. This is one feature across three modules, not a redesign.

Required interfaces and behavior:
- In activity/parse.py add parse_timestamp(text) returning a timezone-aware datetime normalized to UTC. Support ISO timestamps with Z or numeric offsets; reject naive, empty, malformed timestamps with ValueError.
- Keep load_events(path) compatible with existing callers. Timestamps on Event may remain raw text; legacy CSVs without a timestamp column must still work when no window is requested.
- In activity/report.py extend summarize(events, *, since=None, until=None), where bounds are timezone-aware datetimes. A row is included at since and excluded at until. Either bound can be omitted. Normalize offsets for comparison. Reject naive bounds, and since >= until with ValueError. With an active window, every event must have a valid aware timestamp, even if another event would be excluded. Without bounds preserve legacy output and ignore timestamp validity.
- In activity/cli.py add --since and --until flags parsed via parse_timestamp. Validation/data errors return exit code 2, useful stderr, and no JSON stdout. Success emits the existing single JSON shape: count and category totals, exact Decimal arithmetic, sorted categories. No extra metadata. Preserve invocation via python3 -m activity.cli.
- Add focused tests in tests/test_windows.py. Existing tests/test_legacy.py and package __init__.py must remain unchanged.

Concrete acceptance examples (apply equally to implementation and review):
- A CSV containing `category,amount,timestamp` followed by the short row `a` is a data error, including when no window is requested. Missing amount, an empty amount, and `not-a-number` must produce CLI exit 2, useful stderr without a traceback, and completely empty stdout. Exercise the actual `python3 -m activity.cli` process; an uncaught Python exception returning exit 1 does not satisfy this contract.
- `parse_timestamp('2026-10-10T10:00:00+01:60')` and `parse_timestamp('2026-10-10T10:00:00+24:00')` must raise ValueError. A parser silently normalizing an invalid offset is not sufficient validation. Valid `2026-10-10T12:00:00+02:00` normalizes to `2026-10-10T10:00:00+00:00`.
- `--since bad` must exit 2 with stderr and no stdout. Equal or reversed bounds must also fail on an empty input, rather than returning an empty successful report.
- With an active window, a missing, empty, naive, or malformed event timestamp must fail even when another row is outside the window. A legacy CSV without timestamps must still succeed without bounds, but must fail when a bound is supplied.
Cover these examples with focused tests in the owned test file; preserve the existing success behavior and protected legacy tests. These examples clarify required error semantics, not permission for unrelated hardening.

Inputs: activity/parse.py, activity/report.py, activity/cli.py, tests/test_legacy.py.
Owned paths: activity/parse.py, activity/report.py, activity/cli.py, tests/test_windows.py only.
Acceptance commands: python3 -m unittest discover -s tests -v; python3 -m compileall -q activity tests.
Do not add dependencies, network/GPU operations, commits, or unrelated refactors. Finish once requirements and checks pass; optional improvements are outside scope. Return a concise final report with changed files, checks and material uncertainty.
