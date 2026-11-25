#!/usr/bin/env python3
"""Private-session-only MCP bridge for zClaw memory retrieval."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


ZRAG_URL = os.environ.get("ZRAG_API_URL", "http://api:8200").rstrip("/")
MEMORY_COLLECTION = "zclaw-memory"

TOOLS = [
    {
        "name": "zrag_memory_search",
        "description": (
            "Search private zClaw memory. Register this tool only in the "
            "private main session."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": 1000},
                "limit": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "zrag_memory_source",
        "description": "Fetch bounded source chunks for private zClaw memory search results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "format": "uuid"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
                "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 0},
            },
            "required": ["source_id"],
            "additionalProperties": False,
        },
    },
]


def _read_secret(env_name: str, default_path: str) -> str:
    env_value = os.environ.get(env_name)
    if env_value:
        return env_value
    path = Path(os.environ.get(env_name + "_FILE", default_path))
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError(f"Secret file is empty: {path}")
    return value


def _headers() -> dict[str, str]:
    return {
        "X-Zrag-Token": _read_secret(
            "Z_RAG_API_TOKEN",
            "/work/zrag/infra/secrets/api_token",
        ),
        "X-Zrag-Memory-Token": _read_secret(
            "Z_RAG_MEMORY_API_TOKEN",
            "/work/zrag/infra/secrets/memory_api_token",
        ),
    }


def _request(
    path: str,
    *,
    method: str = "GET",
    body: Any = None,
    query: dict[str, Any] | None = None,
) -> Any:
    url = f"{ZRAG_URL}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method=method)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in _headers().items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"zRAG returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"zRAG memory API unavailable: {exc}") from exc


def _call(name: str, arguments: Any) -> Any:
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be an object")
    allowed = {
        "zrag_memory_search": {"query", "limit"},
        "zrag_memory_source": {"source_id", "limit", "offset"},
    }
    if name not in allowed:
        raise ValueError("Unknown tool")
    if set(arguments) - allowed[name]:
        raise ValueError("Unexpected argument")

    if name == "zrag_memory_search":
        query = arguments.get("query")
        limit = arguments.get("limit", 3)
        if not isinstance(query, str) or not query.strip() or len(query) > 1000:
            raise ValueError("query must contain 1 to 1000 characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5:
            raise ValueError("limit must be an integer from 1 to 5")
        return _request(
            "/v1/search",
            method="POST",
            body={"query": query, "collection": MEMORY_COLLECTION, "limit": limit},
        )

    source_value = arguments.get("source_id")
    if not isinstance(source_value, str):
        raise ValueError("source_id must be a UUID")
    try:
        source_id = str(uuid.UUID(source_value))
    except (ValueError, AttributeError) as exc:
        raise ValueError("source_id must be a UUID") from exc
    limit = arguments.get("limit", 10)
    offset = arguments.get("offset", 0)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("limit must be an integer from 1 to 20")
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 10000:
        raise ValueError("offset must be an integer from 0 to 10000")
    quoted_id = urllib.parse.quote(source_id, safe="")
    return _request(
        f"/v1/sources/{quoted_id}",
        query={"collection": MEMORY_COLLECTION, "limit": limit, "offset": offset},
    )


def _content(value: Any, *, error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}],
        "isError": error,
    }


def _reply(request_id: Any, result: Any) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}) + "\n")
    sys.stdout.flush()


def _reply_error(request_id: Any, code: int, message: str) -> None:
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _reply_error(None, -32700, "Parse error")
            continue
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
            _reply_error(None, -32600, "Invalid Request")
            continue
        request_id = request.get("id")
        method = request.get("method")
        if method == "initialize":
            _reply(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "zclaw-private-memory", "version": "1.0.0"},
            })
        elif method == "ping":
            _reply(request_id, {})
        elif method == "tools/list":
            _reply(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = request.get("params", {})
            try:
                if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                    raise ValueError("tools/call requires a name")
                result = _call(params["name"], params.get("arguments", {}))
                _reply(request_id, _content(result))
            except Exception as exc:
                _reply(request_id, _content(str(exc), error=True))
        elif method in {"notifications/initialized", "notifications/cancelled"}:
            continue
        else:
            _reply_error(request_id, -32601, "Method not found")


if __name__ == "__main__":
    main()
