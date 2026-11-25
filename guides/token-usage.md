# Track zClaw usage

The supported source for historical, per-session and per-model usage is the Gateway `sessions.usage` report. `scripts/usage/token_usage.py` formats a saved report. It does not read session databases, parse Codex logs, estimate tokens from context size, or fetch data itself.

## Export a report

On the Gateway host, identify the current container and save the report outside the repository in a private directory. Use the active agent's configured ID if you want to limit the report to one agent. Omitting the agent scope uses the default agent. `agentScope: "all"` includes every configured agent, so use it only when that is intended.

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Status}}'
sudo install -d -m 700 /opt/zclaw-data/zclaw-usage
sudo docker exec -i <gateway-container> openclaw gateway call sessions.usage \
  --params '{"range":"30d"}' --json \
  > /opt/zclaw-data/zclaw-usage/sessions-usage.json
```

For a scoped export, include `"agentId":"<configured-agent-id>"` in the JSON parameters. Choose a range that fits your reporting question. The Gateway report can be partial or still computing; check `partial`, `cacheStatus`, and each session's `computing` and `usage` fields.

The Gateway exposes per-session reports with totals, per-model attribution, and daily data. `totalTokens` is the runtime's recorded token basis. Cost may be provider-reported or locally estimated, so treat it as a usage cost value, not account billing or quota. A null usage row is unknown or pending, not zero. See the [usage and cost reference](https://docs.openclaw.ai/reference/token-use), [session usage RPC types](https://github.com/openclaw/openclaw/blob/main/src/shared/usage-types.ts), and [usage field definitions](https://github.com/openclaw/openclaw/blob/main/src/infra/session-cost-usage.types.ts).

## Format and retain the report

Run the formatter from the zClaw repository on the saved file:

```bash
python3 scripts/usage/token_usage.py \
  /opt/zclaw-data/zclaw-usage/sessions-usage.json

python3 scripts/usage/token_usage.py \
  /opt/zclaw-data/zclaw-usage/sessions-usage.json \
  --format json
```

Keep the original JSON and any generated report in private storage. Session identifiers and channel metadata are sensitive. Do not commit exports or post them publicly. Reports with overlapping date ranges overlap in their totals; do not add those totals together. For comparisons, use matching date windows, runtime versions, model routes, and task sets, and record when the Gateway marks data partial or computing.

This report tracks usage by session and model. It does not infer which delegated role produced a session unless the Gateway itself provides that attribution, and it does not measure account plan limits. Provider quota windows are a separate usage surface.
