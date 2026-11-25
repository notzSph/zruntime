import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plus_profile_is_luna_first():
    profile = json.loads((ROOT / "profiles/plus/profile.json").read_text())
    assert profile["root"] == {"model": "openai/gpt-6-luna", "thinking": "max"}
    assert profile["workers"] == {"model": "openai/gpt-6-luna", "thinking": "medium"}
    assert profile["reviewer"] == {
        "model": "openai/gpt-6-astra", "thinking": "low", "readOnly": True
    }
    assert profile["maxConcurrentSubagents"] == 4
    assert profile["roles"] == ["explorer", "worker", "tester", "researcher", "reviewer"]


def test_zclaw_workflow_guides_exist():
    for name in (
        "plus-plan",
        "full-orchestration",
        "routine-coding",
        "fast-iteration",
        "complex-repo-work",
        "token-usage",
    ):
        assert (ROOT / "guides" / f"{name}.md").is_file()


def test_role_prompts_exist_and_are_not_codex_toml():
    for role in ("explorer", "worker", "tester", "researcher", "reviewer"):
        assert (ROOT / "orchestration/roles" / f"{role}.md").is_file()
        assert not (ROOT / "orchestration/roles" / f"{role}.toml").exists()


def test_orchestrator_covers_delegation_failure_and_final_checks():
    skill = (ROOT / "skills/zclaw-orchestrator/SKILL.md").read_text()
    assert "Maximum four concurrent child runs" in skill
    assert "read-only" in skill
    assert "If `sessions_spawn` is unavailable" in skill
    assert "Do not accept child work until" in skill
    assert "Before claiming completion" in skill


def test_usage_guide_uses_gateway_reports_and_repeatable_runs():
    guide = (ROOT / "guides/token-usage.md").read_text()
    assert "token_usage.py" in guide
    assert "context-window snapshots" in guide
    assert "sessions.usage" in guide


def test_zclaw_usage_report_tool_is_active():
    assert (ROOT / "scripts/usage/token_usage.py").is_file()
    assert (ROOT / "tests/test_token_usage.py").is_file()


def test_adapter_protocol():
    result = subprocess.run(
        [sys.executable, str(ROOT / "mcp" / "zjev_zrag_mcp.py")],
        input='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n',
        text=True,
        capture_output=True,
        check=True,
    )
    names = {tool["name"] for tool in json.loads(result.stdout)["result"]["tools"]}
    assert {"zrag_search", "zrag_source", "zjev_job_fit", "zjev_target_plan"} <= names


def test_patch_validates_against_live_schema():
    import os

    container = os.environ.get("ZCLAW_GATEWAY_CONTAINER")
    runtime_path = os.environ.get("ZCLAW_RUNTIME_PATH")
    if not container or not runtime_path:
        import pytest

        pytest.skip("set ZCLAW_GATEWAY_CONTAINER and ZCLAW_RUNTIME_PATH for live Gateway validation")

    command = [
        "sudo", "docker", "exec", container,
        "openclaw", "config", "patch",
        "--file", f"{runtime_path}/profiles/plus/gateway.patch.json5",
        "--dry-run",
    ]

    result = subprocess.run(
        command,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Dry run successful" in result.stdout
