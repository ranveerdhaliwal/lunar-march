Migrate the public reporting API from `summarize` to `summarize_events`, across five files. This is a compatibility migration, not a behavior change.

Requirements:
- In activity/report.py move the existing implementation to summarize_events(events). Keep summarize(events) as a thin compatibility wrapper that calls the current module-level summarize_events, returning its result unchanged. No duplicated implementation or warnings.
- In activity/cli.py and activity/service.py import and call summarize_events by that name. Preserve their current signatures, JSON, exit/error behavior and CSV handling.
- Export both summarize_events and the compatibility summarize from activity/__init__.py.
- Update README.md to show the canonical import from activity, explain the legacy wrapper, and retain the service and CLI usage.
- Preserve exact Decimal arithmetic, count, sorted category keys, empty-input behavior and input immutability. Accepted inputs remain lists of existing Event objects. No timestamp feature, new validation, dependencies or unrelated hardening.

Protected executable acceptance checks are already supplied in acceptance/test_contract.py. Read them alongside the implementation before editing. They settle the concrete compatibility and caller contracts and must not be edited. tests/test_legacy.py and activity/parse.py are also protected. No new files are required.

Owned paths (all five require changes): activity/report.py, activity/cli.py, activity/service.py, activity/__init__.py, README.md.
Acceptance commands:
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s acceptance -v
python3 -m compileall -q activity tests acceptance

CPU only. Do not use network/GPU operations, install dependencies, commit, add workflow artifacts or delegate. Finish when the stated migration and checks pass. Return changed paths, checks and any unmet requirement concisely.
