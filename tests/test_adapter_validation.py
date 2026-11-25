import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "mcp" / "zjev_zrag_mcp.py"


def run_adapter(lines):
    result = subprocess.run(
        [sys.executable, str(ADAPTER)],
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line]


def test_tool_limits_are_enforced_before_network_call():
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "zrag_search", "arguments": {"query": "x", "limit": 11}},
    }
    response = run_adapter([json.dumps(request)])[0]
    assert response["result"]["isError"] is True
    assert "from 1 to 10" in response["result"]["content"][0]["text"]


def test_malformed_json_does_not_stop_server():
    response = run_adapter(["{bad", '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'])
    assert response[0]["error"]["code"] == -32700
    assert response[1]["id"] == 2
    assert "tools" in response[1]["result"]


def test_unknown_method_uses_json_rpc_error_envelope():
    request = {"jsonrpc": "2.0", "id": 7, "method": "not/a-method"}
    response = run_adapter([json.dumps(request)])[0]
    assert response["error"]["code"] == -32601
    assert "result" not in response


def test_notification_does_not_get_a_response():
    notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    assert run_adapter([json.dumps(notification)]) == []
