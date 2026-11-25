# Plus profile for zClaw

The Plus profile is a repository package describing a desired zClaw setup. It does not show that the live Gateway has the models, files, credentials, plugins, or services needed to run it. Treat runtime inventory and health as snapshots and recheck them before each activation.

## Package contents and intent

- `profiles/plus/profile.json` is a human-readable manifest. zClaw does not load it directly.
- `profiles/plus/gateway.patch.json5` is a proposed Gateway config patch, not the active configuration.
- `skills/zclaw-orchestrator/SKILL.md` describes zClaw's root-agent behavior.
- `orchestration/roles/*.md` are prompt material for child tasks. They are not automatically loaded agent definitions.
- The patch requests `openai/gpt-6-luna` for root and execution roles, max global thinking, up to four concurrent child runs, SearXNG, and a `zjev-zrag` MCP process. Astra is only needed for the optional reviewer role.

These are package settings, not evidence of account access or route support. The workspace CLI inspection available for this guide found only `openai/gpt-5.5` in the model list and did not find `~/.zclaw/zclaw.json`. That does not establish the state of the target Gateway or prove that the Plus profile is active. Recheck the actual target before making any claim about its configuration.

## Host and Gateway access

Use the actual host checkout paths for runtime tools and the zClaw source. A repository checkout is not automatically mounted inside the Gateway container. Never put a host path into Gateway configuration unless that exact path exists inside the container.

Run every Docker CLI command with `sudo`. First identify the current container names, status, ports, mounts, and networks:

```bash
sudo docker ps
GATEWAY_CONTAINER="replace-with-current-gateway-container"
sudo docker inspect --format 'name={{.Name}} image={{.Config.Image}} state={{.State.Status}} ports={{json .NetworkSettings.Ports}} mounts={{json .Mounts}} networks={{json .NetworkSettings.Networks}}' "$GATEWAY_CONTAINER"
```

The `--format` inspection shows mount destinations and network aliases without dumping the container's full environment, which may contain secrets. Use the current `sudo docker ps` names when inspecting service containers.

Do not rely on remembered container names, health, port mappings, or service availability. A host's loopback-published port is not automatically a container-to-container endpoint. Inspect shared-network aliases and test reachability from the Gateway container. Discover and verify the zJev endpoint; do not guess a URL.

Run zClaw CLI commands through the Gateway container, never as a bare host command. The required form is:

```bash
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw models list
```

Confirm the container name from the current `sudo docker ps` output before using this example. Use this same `sudo docker exec -it <current-gateway-container> openclaw ...` form for each CLI check below.

## Activation gates

Do not apply the patch until each applicable gate passes:

1. **Mount paths:** Inspect the Gateway container's mounts and networks. Confirm the skill directory and MCP script are present at their configured in-container paths. The patch resolves `${ZCLAW_RUNTIME_PATH}` for the skill directory and MCP script. Set that variable to the path where this repository is mounted inside the Gateway container.
2. **Models:** Run `sudo docker exec -it "$GATEWAY_CONTAINER" openclaw models list` and verify the requested Luna route. Verify Astra only if enabling the reviewer. A missing route blocks activation. Do not silently substitute another model.
3. **Config and schema:** Inspect the live config path and current settings with the Gateway CLI. Run the package's offline checks from the host runtime checkout, then validate the adjusted patch using the installed Gateway CLI. A schema pass does not prove a model request or service call works.
4. **Preserve current settings:** Compare every patch field with the live config. Merge existing values that must remain, especially plugin allowlists, skill directories, and other arrays that may be replaced. Keep a private backup before applying changes.
5. **Services and secrets:** Verify reachability from the Gateway's Docker network and set actual SearXNG, zRAG, and zJev endpoints. Set `SEARXNG_BASE_URL`, `ZRAG_API_URL`, and `ZJEV_API_URL` to addresses verified from the Gateway container network. Provide `Z_RAG_API_TOKEN` and `ZJEV_API_TOKEN` via the Gateway private environment; keep credentials and live config out of this repository.

If a gate fails, record the missing route, path, setting, or service and do not activate the profile until corrected.

## Preflight, rollout, and rollback

Run read-only checks through the current Gateway container:

```bash
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw config file
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw config validate
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw models list
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw skills list
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw health --verbose
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw status --deep
```

These report the selected config path, schema validity, advertised model catalog, installed skills, and Gateway health. They do not prove a particular model request succeeds, a private service is reachable, or an MCP tool works. Check each live value changed by the patch. Replace the container name if current inventory differs.

Place the reviewed patch at a path visible inside the Gateway container. Confirm that path before running the dry run:

```bash
sudo docker exec -it "$GATEWAY_CONTAINER" openclaw config patch --file /verified/container/path/profiles/plus/gateway.patch.json5 --dry-run
```

Use the deployment's documented procedure to back up the private config, apply the reviewed patch, and restart the correct Gateway service. The package does not establish the Compose project, host config path, service name, or restart owner. Discover them from the current deployment instead of reusing a stale guess. Do not edit live config until the activation gates pass and a restorable backup exists.

After applying and restarting, repeat the health, model, and skill checks. Confirm the intended skill is loaded in the target agent's workspace. Send a small request through each selected model route, and verify search and MCP tools from a live agent session. For each MCP server, confirm tool discovery and run a bounded read-only call. Test zRAG retrieval and zJev analysis only when those services are included. Config validation or an HTTP health response alone is not a complete smoke check.

For rollback, restore the exact pre-change private config using the deployment's recovery procedure, validate it, restart the correct Gateway service, and confirm health. Record the backup location and rollback result privately. Editing this repository or restoring the package patch does not roll back live Gateway state.
