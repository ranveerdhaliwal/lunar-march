# Isolated CLI startup fix, 2026-10-10

**Runtime isolation worked in the live parallel trial. Workflow acceptance still failed, so no fresh Direct comparison was purchased.** The two Luna workers and Astra review completed without the earlier shared-config error. No shared configuration, authentication file or daemon was modified by the fix; the installed LunarMarch skill remains disabled. No commit or push.

| Stage | Elapsed |
|---|---:|
| JSONL Luna worker | 99.950 s |
| CSV Luna worker | 45.145 s |
| Overlapping worker phase, including dispatch/checks | 100.092 s |
| Astra integration review | 45.237 s |
| Whole parallel workflow | 145.589 s |

Total trial weighted cost: **10.0693015 Standard credits**. Worker invocation intervals overlapped for 45.146 seconds. These are measured whole-workflow costs to rejection, not accepted-completion savings. Authentication setup/cleanup, merge, combined checks and review are included. Setup/test authoring/controller, external approval review and post-run graders are excluded.

## Scoped fix and protection of other chats

Each model invocation gets a fresh private directory under ignored `.lunarmarch/isolated-runtime`, with mode 0700 and an auth file mode 0600. The launcher reads existing session metadata without modifying it, verifies enough access-token lifetime remains, and copies only access/id/account fields. The private refresh token is empty, so this helper cannot rotate the shared login's refresh credential. Short-lived or unreadable sessions fail without changing login. Child-only CODEX_HOME and CODEX_SQLITE_HOME point into the private directory; inherited CODEX_* routing variables and OPENAI_API_KEY are removed from that child environment. No parent-process environment is changed.

The CLI receives `--no-daemon` and `--ignore-user-config`. Model, effort and Standard tier are explicit. Private runtime files are removed after each invocation, including failure. No active daemon was stopped/restarted, no other chat was messaged, and GPU processes/repositories were untouched. The same account still pays for model usage; this is state isolation, not separate account quota.

The implementation uses controls checked against installed CLI help and the official [CLI reference](https://learn.chatgpt.com/docs/cli/reference), [environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables), and [authentication documentation](https://learn.chatgpt.com/docs/auth). Manual stripped auth-record compatibility is locally validated here, not guaranteed by those docs. The access-token login command rejected this cached ChatGPT token format; that attempt did not reach a model or change shared state.

## Validation and retained failures

Two concurrent login-status probes and two concurrent prompt-render/config probes passed without model generation. Shared config/auth hashes stayed unchanged during those probes. Refresh credentials were absent, private permissions correct and temporary homes removed. All 65 offline tests passed, including scoped launch flags, credential filtering, token lifetime refusal, cleanup, concurrent dispatch, merge boundaries, complete accounting and reviewer mutation rejection.

The first live isolated attempt failed before telemetry in both workers because my wrapper retained a Docker-MCP disable override despite having no MCP server definition in the private runtime. This produced `invalid transport`. I removed that override only for isolated calls and preserved the failed run under `/tmp/lunarmarch-parallel-isolated-20261010`. It is not relabeled as success. The corrected trial is separate and frozen under `/tmp/lunarmarch-parallel-isolated-pair-20261010`. Five live launch attempts occurred this turn: two failed configuration starts and three completed model calls. Missing usage for the two failures is unknown, not zero.

The corrected plan was limited to one pair, at most four new calls, with 180 seconds per worker, 120 seconds review and 240 seconds Direct. Runtime or quality failure stops further spending. Both workers passed, merged files stayed inside their declared paths, and review changed no source. All 20 unit tests, 16 protected acceptance tests, three post-run probes and compilation passed.

Astra nevertheless rejected the CSV formatter because a JSON tag array containing a 5,000-digit integer raises ValueError without the required row context. It still rejects the input; this is a narrow diagnostic requirement failure, not observed data corruption or successful acceptance of bad input. Independent local reproduction confirms it. The historical Direct output, from a different runtime, includes the row context for the same input. That post-hoc comparison is not a fresh timing/cost baseline. No repair, extra Direct call or further model retry followed.

Exact frozen hashes, flags, telemetry, overlap, failure records, source, prompts and probe evidence are in [the JSON record](2026-10-10-isolated-runtime.json). Shared-state probes show no modifications by those probes; concurrent user chats can still independently change shared files. This local success does not establish universal startup reliability or justify re-enabling the skill. A focused opt-in benchmark can request the isolated mode with `scripts/parallel_eval.py prepare --isolated-runtime`; this does not change ordinary Codex settings.
