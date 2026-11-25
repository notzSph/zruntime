# zRuntime

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Build](https://img.shields.io/badge/Build-passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.14.4-3776AB)
![PR](https://img.shields.io/badge/PRs-Welcome-green)
![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey)

zRuntime is zClaw's companion package for agent orchestration, MCP integrations, and runtime deployment guidance. It provides reusable role prompts and profiles, bounded zRAG and zJev integrations, and tools for inspecting Gateway usage reports.

The configuration here describes an intended setup. It does not prove that a running Gateway has loaded the configuration or can reach its model and service dependencies.

## Plus profile

`profiles/plus/profile.json` is the human-readable topology manifest. The Gateway does not load it directly. `profiles/plus/gateway.patch.json5` is the proposed Gateway configuration patch. Keep the two aligned when the profile changes.

The intended topology is:

- Root agent: `openai/gpt-6-luna`, maximum reasoning.
- Explorer, worker, tester, and researcher: `openai/gpt-6-luna`, medium reasoning.
- Optional reviewer: `openai/gpt-6-astra`, low reasoning, read-only.
- Up to four concurrent child sessions per spawning session, subject to the active runtime's supported controls.
- Web search through the configured SearXNG provider.
- `zjev-zrag` MCP server for bounded zRAG retrieval and zJev analysis.

These are target settings, not guarantees of account access or model routing. Verify models, tools, and service reachability against the target Gateway before activation. Select the reviewer model and enforce its read-only permissions per child when spawning it; the global subagent default does not select Astra or enforce reviewer permissions automatically.

## Package map

- `skills/zclaw-orchestrator/SKILL.md`: root orchestration workflow and operating rules.
- `orchestration/roles/`: child task prompts. Include the relevant prompt in each child task; these files are not automatically loaded as agent definitions.
- `profiles/plus/profile.json`: declarative profile manifest.
- `profiles/plus/gateway.patch.json5`: proposed Gateway configuration patch.
- `mcp/zjev_zrag_mcp.py`: bounded zRAG retrieval and zJev analysis server.
- `mcp/zjev_zrag_memory_mcp.py`: private-session memory server code. It is not registered in the current patch.
- `guides/`: workflow, deployment, and usage guidance.
- `scripts/usage/token_usage.py`: summarizes a saved Gateway `sessions.usage` report.
- `scripts/test/validate.sh` and `tests/`: package checks.
- `requirements-test.txt`: Python test dependency.

## Deployment boundaries

The patch uses `${ZCLAW_RUNTIME_PATH}` for its skill and MCP script locations. Set it to the repository path as mounted inside the Gateway container. Set `SEARXNG_BASE_URL`, `ZRAG_API_URL`, and `ZJEV_API_URL` to verified container-reachable endpoints, and supply `Z_RAG_API_TOKEN` and `ZJEV_API_TOKEN` through the Gateway’s private environment. Host and workspace checkout paths are not automatically available inside the Gateway container.

The MCP process requires reachable zRAG and zJev endpoints and private credentials supplied through the Gateway environment. Keep tokens and live Gateway configuration out of this repository. The patch leaves endpoint values to verified environment variables because Docker network aliases are deployment-specific.

The runtime CLI executable is `openclaw`; invoke it through the verified Gateway container and prefix Docker commands with `sudo`. Do not apply the patch until the model routes, mount paths, current configuration, service endpoints, and rollback backup are verified.

For read-only preflight, rollout, smoke checks, and rollback, follow [the Plus deployment guide](guides/plus-plan.md). Do not claim the profile is active based on a successful config dry-run alone.

## Repository layout

```text
.
├── guides/
├── mcp/
├── orchestration/roles/
├── profiles/plus/profile.json
├── profiles/plus/gateway.patch.json5
├── requirements-test.txt
├── scripts/
│   ├── usage/token_usage.py
│   ├── test/validate.sh
│   └── setup/
├── skills/zclaw-orchestrator/SKILL.md
├── tests/
└── README.md
```

The usage tool summarizes saved per-session and per-model usage reported by zClaw. It does not infer token counts from context size, and its cost field is not provider billing or plan quota. See [usage tracking](guides/token-usage.md).

## Scripts

- `scripts/usage/token_usage.py` formats a saved Gateway `sessions.usage` JSON report. See [usage tracking](guides/token-usage.md).
- `scripts/test/validate.sh` runs the repository's automated checks.
