#!/usr/bin/env python3
"""Summarize a saved zClaw Gateway session-usage report.

Export a `sessions.usage` JSON report from the Gateway, then pass its path to
this script. The report is not fetched automatically, and this tool does not
read Gateway databases or infer usage from context-window snapshots.

Usage:
  python3 scripts/usage/token_usage.py REPORT.json [--format md|json]

The Gateway report can include private session metadata. Keep source reports
and generated output in a private directory, outside the repository.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


TOKEN_FIELDS = ("input", "output", "cacheRead", "cacheWrite", "totalTokens")
COST_FIELDS = (
    "inputCost",
    "outputCost",
    "cacheReadCost",
    "cacheWriteCost",
    "totalCost",
)


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _read_totals(value: Any) -> dict[str, int | float | None]:
    source = value if isinstance(value, dict) else {}
    return {
        key: _number(source.get(key))
        for key in (*TOKEN_FIELDS, *COST_FIELDS)
    }


def load_report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read report file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc

    if isinstance(value, dict) and isinstance(value.get("result"), dict):
        value = value["result"]
    if not isinstance(value, dict) or not isinstance(value.get("sessions"), list):
        raise ValueError("expected a Gateway sessions.usage result with a sessions array")
    return value


def normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    sessions = []
    computing = 0
    unavailable = 0

    for row in report["sessions"]:
        if not isinstance(row, dict):
            continue
        usage = row.get("usage")
        if not isinstance(usage, dict):
            usage = None
            if row.get("computing"):
                computing += 1
            else:
                unavailable += 1

        model_usage = []
        raw_model_usage = usage.get("modelUsage", []) if usage else []
        if isinstance(raw_model_usage, list):
            for model_row in raw_model_usage:
                if not isinstance(model_row, dict):
                    continue
                model_usage.append(
                    {
                        "provider": model_row.get("provider"),
                        "model": model_row.get("model"),
                        "count": _number(model_row.get("count")),
                        "totals": _read_totals(model_row.get("totals")),
                    }
                )

        sessions.append(
            {
                "sessionId": row.get("sessionId"),
                "key": row.get("key"),
                "label": row.get("label"),
                "agentId": row.get("agentId"),
                "channel": row.get("channel"),
                "modelProvider": row.get("modelProvider"),
                "model": row.get("model"),
                "computing": bool(row.get("computing")),
                "usage": _read_totals(usage) if usage else None,
                "modelUsage": model_usage,
            }
        )

    aggregates = report.get("aggregates")
    if not isinstance(aggregates, dict):
        aggregates = {}

    by_model = []
    raw_by_model = aggregates.get("byModel", [])
    if not isinstance(raw_by_model, list):
        raw_by_model = []
    for model_row in raw_by_model:
        if not isinstance(model_row, dict):
            continue
        by_model.append(
            {
                "provider": model_row.get("provider"),
                "model": model_row.get("model"),
                "count": _number(model_row.get("count")),
                "totals": _read_totals(model_row.get("totals")),
            }
        )

    partial = report.get("partial")
    cache_status = report.get("cacheStatus")
    return {
        "startDate": report.get("startDate"),
        "endDate": report.get("endDate"),
        "updatedAt": _number(report.get("updatedAt")),
        "cacheStatus": cache_status.get("status") if isinstance(cache_status, dict) else None,
        "partial": partial,
        "totals": _read_totals(report.get("totals")),
        "sessionCount": _number(aggregates.get("sessionCount")),
        "computingRows": computing,
        "unavailableRows": unavailable,
        "byModel": by_model,
        "sessions": sessions,
    }


def _fmt(value: int | float | None) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        return f"{int(value):,}"
    return f"{value:,.4f}"


def render_markdown(summary: dict[str, Any]) -> str:
    totals = summary["totals"]
    period = f"{summary['startDate'] or '?'} to {summary['endDate'] or '?'}"
    lines = ["# zClaw session usage", "", f"Period: {period}"]
    if summary["cacheStatus"]:
        lines.append(f"Report cache: {summary['cacheStatus']}")
    if summary["partial"]:
        lines.append("Report is partial. Do not treat these totals as complete.")
    if summary["computingRows"] or summary["unavailableRows"]:
        lines.append(
            f"Rows without settled usage: {summary['computingRows']} computing, "
            f"{summary['unavailableRows']} unavailable."
        )

    lines.extend(
        [
            "",
            "## Totals",
            "",
            "| Input | Output | Cache read | Cache write | Total tokens | Recorded or estimated cost |",
            "|---:|---:|---:|---:|---:|---:|",
            "| "
            + " | ".join(
                _fmt(totals.get(field))
                for field in (*TOKEN_FIELDS, "totalCost")
            )
            + " |",
            "",
            "## By model",
            "",
            "| Provider | Model | Calls | Input | Output | Cache read | Cache write | Total tokens | Cost |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for row in summary["byModel"]:
        model_totals = row["totals"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("provider") or "unknown"),
                    str(row.get("model") or "unknown"),
                    _fmt(row.get("count")),
                    *(_fmt(model_totals.get(field)) for field in TOKEN_FIELDS),
                    _fmt(model_totals.get("totalCost")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Sessions",
            "",
            "| Session | Agent | Channel | Model | Total tokens | Cost | Usage state |",
            "|---|---|---|---|---:|---:|---|",
        ]
    )
    for row in summary["sessions"]:
        usage = row["usage"] or {}
        session_id = row.get("sessionId") or row.get("key") or row.get("label") or "unknown"
        model = row.get("model") or "unknown"
        state = (
            "computing"
            if row["computing"]
            else "available"
            if row["usage"] is not None
            else "unavailable"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(session_id),
                    str(row.get("agentId") or "unknown"),
                    str(row.get("channel") or "unknown"),
                    str(model),
                    _fmt(usage.get("totalTokens")),
                    _fmt(usage.get("totalCost")),
                    state,
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append(
        "Cost is a Gateway-reported or locally estimated usage value, not provider billing or plan quota."
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="saved Gateway sessions.usage JSON report")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = normalize_report(load_report(args.report))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
