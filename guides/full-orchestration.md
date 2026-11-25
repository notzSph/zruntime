# Full orchestration

Use the full lifecycle for multi-file changes, cross-component debugging, research-heavy work, or tasks that explicitly request agents. Keep small, local, low-risk work in the root session.

## zClaw runtime and authority

zClaw should be direct, execution-focused, and evidence-led. Use the available zClaw session and web tools when they are actually exposed; do not assume zRAG, zJev, a model route, or a connected node is available because the package mentions it. An authoring-environment inspection on 2026-11-25 found no `~/.zclaw/zclaw.json` and advertised only `openai/gpt-5.5`. That dated observation does not establish the current state of the target Gateway. Recheck before selecting the Plus model.

Keep private data private. Do not impersonate z or cause external side effects without action-specific authorization. For VPS or security changes, inspect read-only first, analyze the result, and make a stepwise plan before applying changes. zClaw may edit and verify repository files; z owns commits, pushes, branch syncing, and history unless explicitly overridden for that action.

## Before delegation

Check the active session and available zClaw tools. The package describes a Plus target, not a guarantee about the running deployment. Delegate only if `sessions_spawn` is available, and only request a model that the active runtime can route. The configured Plus models are `openai/gpt-6-luna` for the root and execution roles, and `openai/gpt-6-astra` for optional review. If the model list or a spawn error does not confirm availability, report the limitation and continue in the current session only if it can complete the work safely. Never silently substitute a model or claim a child ran when it did not.

Treat the Plus setup as inactive until the required model routes, mounted files, and tools are confirmed in the target deployment. A profile manifest or config patch in this repository does not establish live capability. Recheck these conditions after runtime, model, or deployment changes.

## Lifecycle and decision gates

1. **Classify the task.** Keep it root-only if delegation would not materially improve coverage or independent verification. For delegated work, identify separate, useful workstreams.
2. **Explore read-only.** Assign bounded areas to explorers. Require relevant paths and symbols, evidence, constraints, and risks. For current external behavior, use a researcher only when live search/fetch is actually available; otherwise mark the fact unverified.
3. **Set the design and ownership.** The root resolves conflicting evidence, chooses scope, defines acceptance checks, and assigns non-overlapping file ownership before implementation. Pause delegation if the evidence requires a wider architecture or security decision.
4. **Implement.** Give each worker one bounded objective. Include the worker role prompt from `orchestration/roles/worker.md` in the child task because zClaw does not automatically load these Markdown role files. Include exact editable paths, constraints, deliverables, and acceptance criteria.
5. **Verify.** Use a tester for independent reproduction when the task warrants it. The tester role prompt is guidance, not a runtime permission boundary. The root remains responsible for the final diff and checks.
6. **Review when useful.** For material security, compatibility, or data-integrity risk, request a read-only reviewer pass on the actual diff. This profile specifies Astra at low thinking for that role. Do not request it unless the model route is confirmed and the task benefits from independent review.
7. **Integrate and report.** Wait for required children to complete. Inspect their changed paths and findings, resolve material issues, run the checks appropriate to the task, and report exact results and remaining uncertainty.

## Child task and failure handling

Each `sessions_spawn` task should state the objective, owned paths or read-only boundary, relevant context, constraints, deliverable, and acceptance criteria. Set the role model and thinking explicitly only where the runtime supports those options. Keep the total concurrent child runs at or below the configured limit of four; this is a package target and must be checked against the active runtime.

If spawning is unavailable, rejected, or returns an unexpected model, capture the exact failure. Do not retry by silently changing models. Continue root-only when safe, or stop and explain what capability blocks completion. If a child fails or returns incomplete evidence, inspect its result and either narrow/reassign the work or handle the bounded part in the root. Do not accept implementation without knowing the actual scope, changed files, validation performed, and unresolved risks.

On the target host, Docker commands require `sudo`, and zClaw CLI commands must run through the Gateway container. Verify current container names and health before running commands. Use actual host checkout paths; do not pass container paths as host paths. See [Plus deployment preflight](plus-plan.md) for the zClaw commands.

Use zRAG only if its MCP tools are present and responding; preserve returned citations and locators. Use zJev only through the bounded tools exposed by the configured MCP server. Use web search for current external facts only when the configured search/fetch tools work, and cite direct sources. A config entry or successful schema validation alone proves none of these services are reachable.
