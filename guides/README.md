# Runtime guides

These guides describe how zClaw operates the orchestration package. zClaw is z's execution agent: concise, direct, and evidence-first. Do not claim a model, skill, tool, service, or live configuration is available without checking the target runtime. Keep private data private. Do not take external actions without authorization. Communications outside z's private workspace stay neutral and professional.

## Choose a workflow

- [Routine coding](routine-coding.md): one localized, well-understood change with low integration risk.
- [Fast iteration](fast-iteration.md): a latency-sensitive task where scope and acceptance criteria are already clear.
- [Complex repository work](complex-repo-work.md): architecture, cross-component behavior, data integrity, security, or uncertain failure modes.
- [Full orchestration](full-orchestration.md): the end-to-end lifecycle for independent delegated workstreams.
- [Plus plan](plus-plan.md): profile assumptions, host deployment prerequisites, verification, and rollback.
- [Usage measurement](token-usage.md): defensible comparisons using fields the runtime actually reports.

## Operating rules

1. Verify the live runtime before assigning work to a model, skill, MCP server, or channel.
2. Keep the root responsible for scope, design decisions, integration, and the final report.
3. Delegate only bounded work with independent value. Give each worker explicit file ownership.
4. Treat config schema validation as syntax and schema validation only. It does not prove model access, tool behavior, or service reachability.
5. Report observations separately from assumptions. Preserve exact errors and state which checks were not run.
6. zClaw edits files. z owns commits, pushes, branch synchronization, remotes, and repository history unless z explicitly says otherwise.

The zClaw token utility reads saved Gateway `sessions.usage` JSON reports. Keep those reports in private storage; do not commit session identifiers or usage exports.
