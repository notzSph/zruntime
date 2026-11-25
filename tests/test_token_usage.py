import json
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.usage.token_usage import load_report, normalize_report, render_markdown


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "usage" / "token_usage.py"


def make_report():
    return {
        "startDate": "2026-11-01",
        "endDate": "2026-11-25",
        "updatedAt": 1_795_585_200_000,
        "cacheStatus": {"status": "fresh"},
        "totals": {
            "input": 1200,
            "output": 300,
            "cacheRead": 100,
            "cacheWrite": 20,
            "totalTokens": 1620,
            "totalCost": 0.0125,
        },
        "aggregates": {
            "sessionCount": 2,
            "byModel": [
                {
                    "provider": "openai",
                    "model": "gpt-6-luna",
                    "count": 4,
                    "totals": {
                        "input": 1200,
                        "output": 300,
                        "cacheRead": 100,
                        "cacheWrite": 20,
                        "totalTokens": 1620,
                        "totalCost": 0.0125,
                    },
                }
            ],
        },
        "sessions": [
            {
                "key": "agent:main:main",
                "sessionId": "session-main",
                "agentId": "main",
                "channel": "discord",
                "modelProvider": "openai",
                "model": "gpt-6-luna",
                "usage": {
                    "input": 1200,
                    "output": 300,
                    "cacheRead": 100,
                    "cacheWrite": 20,
                    "totalTokens": 1620,
                    "totalCost": 0.0125,
                    "modelUsage": [
                        {
                            "provider": "openai",
                            "model": "gpt-6-luna",
                            "count": 4,
                            "totals": {
                                "input": 1200,
                                "output": 300,
                                "cacheRead": 100,
                                "cacheWrite": 20,
                                "totalTokens": 1620,
                                "totalCost": 0.0125,
                            },
                        }
                    ],
                },
            },
            {
                "key": "agent:main:subagent:worker",
                "sessionId": "session-worker",
                "agentId": "main",
                "channel": "discord",
                "computing": True,
                "usage": None,
            },
        ],
    }


def test_normalize_report_preserves_measured_totals_and_partial_rows():
    summary = normalize_report(make_report())

    assert summary["totals"]["totalTokens"] == 1620
    assert summary["totals"]["totalCost"] == 0.0125
    assert summary["byModel"][0]["model"] == "gpt-6-luna"
    assert summary["sessions"][0]["usage"]["input"] == 1200
    assert summary["sessions"][1]["computing"] is True
    assert summary["computingRows"] == 1


def test_load_report_accepts_gateway_result_envelope():
    with tempfile.TemporaryDirectory() as directory:
        report_path = Path(directory) / "usage.json"
        report_path.write_text(json.dumps({"result": make_report()}), encoding="utf-8")

        report = load_report(report_path)

    assert report["startDate"] == "2026-11-01"
    assert len(report["sessions"]) == 2


def test_markdown_does_not_report_missing_usage_as_zero():
    output = render_markdown(normalize_report(make_report()))

    assert "1 computing, 0 unavailable" in output
    session_rows = output.split("## Sessions", maxsplit=1)[1].splitlines()[3:]
    assert any("| computing |" in line for line in session_rows)
    assert all("| unavailable |" not in line for line in session_rows)
    assert "Cost is a Gateway-reported or locally estimated usage value" in output


def test_cli_emits_json_summary():
    with tempfile.TemporaryDirectory() as directory:
        report_path = Path(directory) / "usage.json"
        report_path.write_text(json.dumps(make_report()), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(report_path), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["sessionCount"] == 2


def test_cli_rejects_non_gateway_json():
    with tempfile.TemporaryDirectory() as directory:
        report_path = Path(directory) / "not-a-report.json"
        report_path.write_text("{}", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(report_path)],
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 2
    assert "sessions array" in result.stderr
