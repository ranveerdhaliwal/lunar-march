# Routing and escalation

## Default ladder

| Work | Model | Effort | Sandbox |
|---|---|---:|---|
| Monitoring, clerical synthesis | Luna | medium | read-only |
| Repository/web research | Luna | medium or high | read-only |
| Bounded implementation | Luna | high | workspace-write |
| Independent review | fresh Luna | high | read-only |
| Difficult adjudication | Luna | xhigh | read-only |
| Consequential unresolved decision | Terra or Sol | high | read-only unless separately authorized |

Use measured evidence to change these defaults. `max` is not a ceremonial quality switch.

## Workflow before model

Choose Direct unless delegation removes substantial work from the parent or satisfies a required evidence boundary. File count and a lower worker price are insufficient reasons. The model table applies after deciding to delegate, not to every user request.

- **Routine coupled work:** parent implementation and targeted verification, including changes spanning several files.
- **Independent bounded work:** Quick with one worker; dispatch a complete packet immediately, then review its diff and recorded checks. Read inputs first only to resolve an actual ambiguity.
- **Unclear scope:** one bounded Scout when its findings are needed before implementation. Do not add a Scout to rediscover a complete task packet.
- **Required durable evidence or consequential risk:** use Task/March and their independent review requirements.

## Concurrency

Start with one worker. Add another only for independent work that can overlap useful parent work or another lane. Keep one writer per checkout; separate writers require non-overlapping ownership and separate worktrees. Workers never delegate. A parent waiting on the only writer has serial delegation, not a parallel speedup.

## Context inheritance

Native subagents have separate context windows. Depending on the host, they may receive all parent turns, a bounded recent window, or no surrounding turns. They share workspace files but do not continuously share the parent's later conversation.

Use the smallest sufficient context:

- Default to no inherited turns plus a compact resolved contract, exact paths, and required evidence.
- Use a small recent-turn window only when recent intent has not yet been captured in durable artifacts.
- Use full-history inheritance only for conversation-dependent interpretation where compression would remove material ambiguity.
- Send new facts explicitly after launch; never assume a worker learned them from the parent automatically.
- Keep worker reports bounded because returned prose also consumes parent synthesis context.

Do not confuse `no inherited turns` with `no context`. The contract and referenced workspace artifacts must still contain every fact needed to perform and verify the task. Missing context and excess context are separate failure modes.

## Escalate when

- two bounded Luna attempts fail the same criterion;
- implementation and review disagree on a material claim;
- evidence remains ambiguous after targeted verification;
- the task crosses architecture, security, data migration, payments, or release boundaries;
- the parent must make a product or authority decision.

Escalation changes the consumer or decision-maker; it does not retroactively validate missing evidence.

## Transport

Prefer native tasks when the host proves the requested model and sandbox were applied. Use external `codex exec` for Luna or `opencode run` for an explicitly selected provider model. Record requested identity as a fact about launch configuration, not proof of remote runtime identity unless session records establish it.

The external launcher starts a fresh conversation and sends only the generated worker packet. This approximates native no-history delegation and makes prompt size inspectable. Native and external results are not interchangeable evidence when their system instructions or tools differ; compare context policies within one transport before comparing transports.

The durable contract, source snapshot, terminal record, gate, and independent-review rule are transport-neutral. The OpenCode adapter supplies a conservative child-agent policy: nested tasks, external directories, web access, and skills are denied; read-only roles also deny edits and shell. OpenCode permissions are not an operating-system sandbox, so use Codex sandboxing or another isolated runtime for hostile or high-risk work. Read [providers.md](providers.md) before selecting or adding a transport.
