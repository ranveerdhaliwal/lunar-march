# Operating modes

Choose the smallest mode that materially improves the work. Ordinary work uses Direct or Quick; Task and March are evidence modes, not automatic coding defaults.

## Direct and Quick

Keep small, tightly dependent work in the parent. For useful ordinary delegation, send one compact packet to one worker and review its result in the parent. The parent must not have implemented the delegated change it accepts. No durable run, separate Reviewer, or phase Auditor is needed merely because multiple files changed. Use Task when recorded independent evidence matters.

For a fully specified Quick assignment, dispatch before reading all implementation files yourself. The worker performs the implementation pass; the parent performs the acceptance pass. Request a concise report, a real diff against the starting snapshot, and exact check results bound to the final files. Review that evidence, reuse unchanged checks, and probe uncovered requirements. Do not treat a worker's self-approval as acceptance or skip independent review for speed. A worker should not load coordinator instructions or create a second workflow. Prefer native dispatch in an interactive chat. For scripted fixed assignments, let the launcher run the worker and then the parent acceptance session; nesting a CLI inside another model's sandbox adds startup and permission failure modes. Skip the acceptance model call when the worker cannot start.

For new disposable Git fixtures, record a baseline commit before dispatch so `git diff` has meaningful content. In an existing dirty checkout, preserve a source snapshot without committing the user's changes.

## Research

Use for broad questions that split into independent angles. Create one shared evidence packet and distinct Scout contracts. Keep Scouts read-only, avoid duplicated questions, and synthesize only after required lanes finish. Missing lanes are missing evidence, not implicit agreement.

Good lane boundaries include subsystems, competing hypotheses, source classes, time periods, or verification dimensions. Parallelize independent work; sequence lanes when later questions depend on earlier findings.

## Task

Use for one bounded mutation or technical deliverable:

```text
optional Scout → Builder → objective gate → independent Reviewer
                                      finding → same-task Fixer → fresh Reviewer of latest snapshot
                                      clear → parent acceptance
```

A Fixer may consume supplied findings. It does not inherit permission to redesign unrelated code. The implementer never reviews itself.

For routine work, use one Reviewer after the Builder and one after a same-task Fixer. Put `max_reviewer_attempts: 2` in the contract. Do not split a small repair into another task solely to create another review cycle. Use a separate task only when ownership, dependencies, rollout, or rollback genuinely needs isolation.

## March

Use when work has multiple reviewable units, dependencies, long waits, or a meaningful chance of interruption. Decompose into phases and tasks. Complete writers before freezing a phase; then run post-barrier verification and a fresh Auditor. Any later phase mutation invalidates the frozen evidence.

Use ordinary event waits for CI, jobs, downloads, or other long waits. Add a Sentinel only when interpretation or recovery requires an agent. Sentinel updates only on material change, completion, or blocker; unchanged state is expected.
