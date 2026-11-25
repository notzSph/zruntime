# Fast iteration

Use this preset when latency matters and the task is reversible, tightly scoped, and easy to validate. Faster execution comes from reducing coordination and limiting the change, not from skipping evidence or checks.

For zClaw, execution-first means removing idle coordination, not guessing. State the objective and the acceptance check, act when the path is clear, and keep the progress report short. If a model, skill, service, or host connection is missing, name that blocker instead of silently substituting a weaker route.

## Qualify the task

Use fast iteration only when all are true:

- The expected behavior and acceptance check are already clear.
- The change has a small, known impact surface.
- A failure is easy to detect and reverse.
- No schema migration, security boundary, data-loss risk, or external side effect is involved.

If any condition fails, use [complex repository work](complex-repo-work.md).

## Run the short path

1. Inspect the relevant files and current working-tree changes. Identify the smallest complete edit.
2. Keep the task in the root session if one person can implement and check it without waiting on independent work. A child adds startup, context, and integration overhead; spawn one only when its output can arrive independently and materially shorten or improve the task.
3. State the acceptance check before editing. Make one focused change, then run the narrow check that covers it.
4. Inspect the diff and the check output. Expand to broader checks if the edit crosses a module boundary or the focused check cannot catch likely regressions.
5. Report the changed behavior and exact check result. If the check was unavailable, say so plainly.

Keep the report to the result, evidence, and any material limitation. Do not commit, push, sync branches, send external messages, or change a live service as an unrequested side effect.

## Use latency controls deliberately

Do not change the global model or thinking defaults to speed up one task. Where the current zClaw runtime exposes a supported per-session thinking control, use a lower level only when the reasoning burden is low. For child sessions, set `model` and `thinking` explicitly in `sessions_spawn` when the task depends on those choices. A configured default is not proof that the intended model is available; check the live model list and report routing errors without silently substituting another model.

Use no more concurrency than the independent work requires. Parallel workers do not speed up serial design, shared-file edits, or integration, and they increase coordination cost. zClaw's `maxConcurrent` applies per spawning session, so it should not be described as a gateway-wide ceiling. See [zClaw subagent configuration](https://docs.openclaw.ai/gateway/config-tools/sessions-and-subagents).

## Stop conditions

Switch to the full workflow if the edit reveals an undocumented contract, a second affected component, unclear ownership, a data migration, or a failure that cannot be checked locally. Do not optimize away the regression check, diff review, or required approval for a live external action.
