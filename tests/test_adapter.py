import json
import os
import subprocess
import sys
from pathlib import Path


def test_mcp_initialize_and_tools_list():
    env = {**os.environ, "ZRAG_API_URL": "http://127.0.0.1:1", "ZJEV_API_URL": "http://127.0.0.1:1"}
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "mcp" / "zjev_zrag_mcp.py"),
        ],
        input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n',
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    rows = [json.loads(line) for line in proc.stdout.splitlines()]
    assert rows[0]["result"]["serverInfo"]["name"] == "zjev-zrag"
    names = {tool["name"] for tool in rows[1]["result"]["tools"]}
    assert {"zrag_search", "zrag_source", "zjev_job_fit", "zjev_target_plan"} <= names
