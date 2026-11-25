#!/usr/bin/env python3
"""Small stdio MCP adapter for the private zRAG and zJev APIs.

The adapter intentionally exposes bounded analysis and retrieval operations.
It does not expose SQL, arbitrary HTTP, CRM export, approval changes, or
outbound messaging.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


ZRAG_URL = os.environ.get("ZRAG_API_URL", "http://api:8200").rstrip("/")
ZJEV_URL = os.environ.get("ZJEV_API_URL", "http://zjev-api:8300").rstrip("/")


def _json_response(value: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "isError": False}


def _error(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def _request(base: str, path: str, *, method: str = "GET", body: Any = None, query: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    url = f"{base}{path}"
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method=method)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"API unavailable at {url}: {exc}") from exc


def _zrag_headers() -> dict[str, str]:
    token = os.environ.get("Z_RAG_API_TOKEN")
    if not token:
        token_file = os.environ.get("Z_RAG_API_TOKEN_FILE", "/work/zrag/infra/secrets/api_token")
        if token_file:
            try:
                token = open(token_file, encoding="utf-8").read().strip()
            except OSError:
                token = None
    if not token:
        raise RuntimeError("Z_RAG_API_TOKEN or Z_RAG_API_TOKEN_FILE is not configured")
    return {"X-Zrag-Token": token}


def _zjev_headers() -> dict[str, str]:
    token = os.environ.get("ZJEV_API_TOKEN")
    if not token:
        raise RuntimeError("ZJEV_API_TOKEN is not configured")
    return {"Authorization": f"Bearer {token}"}


TOOLS = [
    {
        "name": "zrag_search",
        "description": "Search private source-grounded knowledge and return passages with source citations.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "collection": {"type": "string", "default": "ztrading"}, "limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}}, "required": ["query"]},
    },
    {
        "name": "zrag_source",
        "description": "Fetch bounded chunks and metadata for a cited zRAG source.",
        "inputSchema": {"type": "object", "properties": {"source_id": {"type": "string"}, "collection": {"type": "string", "default": "ztrading"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}, "offset": {"type": "integer", "minimum": 0, "default": 0}}, "required": ["source_id"]},
    },
    {
        "name": "zjev_job_fit",
        "description": "Evaluate a CV against a job description through zJev.",
        "inputSchema": {"type": "object", "properties": {"cv": {}, "job_description": {}}, "required": ["cv", "job_description"]},
    },
    {
        "name": "zjev_outreach_evaluate",
        "description": "Evaluate a supplied outreach target using zJev. No message is sent.",
        "inputSchema": {"type": "object", "properties": {"target_profile": {"type": "string"}, "linkedin_activity": {"type": "string"}, "prior_interactions": {"type": "string"}, "offer": {"type": "string"}, "proof_assets": {"type": "array", "items": {"type": "string"}}}, "required": ["target_profile", "linkedin_activity", "offer", "proof_assets"]},
    },
    {
        "name": "zjev_target_plan",
        "description": "Build a bounded, manual target-selection plan through zJev.",
        "inputSchema": {"type": "object", "properties": {"offer": {"type": "string"}, "geography": {"type": "string"}, "company_terms": {"type": "array", "items": {"type": "string"}}, "buyer_titles": {"type": "array", "items": {"type": "string"}}, "priority_signals": {"type": "array", "items": {"type": "string"}}}, "required": ["offer"]},
    },
]


def _call(name: str, args: dict[str, Any]) -> Any:
    _validate_tool_args(name, args)
    if name == "zrag_search":
        return _request(ZRAG_URL, "/v1/search", method="POST", body={"query": args["query"], "collection": args.get("collection", "ztrading"), "limit": args.get("limit", 5)}, headers=_zrag_headers())
    if name == "zrag_source":
        source_id = urllib.parse.quote(args["source_id"], safe="")
        return _request(ZRAG_URL, f"/v1/sources/{source_id}", query={"collection": args.get("collection", "ztrading"), "limit": args.get("limit", 50), "offset": args.get("offset", 0)}, headers=_zrag_headers())
    if name == "zjev_job_fit":
        return _request(ZJEV_URL, "/v1/job_fit", method="POST", body={"cv": args["cv"], "job_description": args["job_description"]}, headers=_zjev_headers())
    if name == "zjev_outreach_evaluate":
        body = {key: args[key] for key in ("target_profile", "linkedin_activity", "offer", "proof_assets")}
        if args.get("prior_interactions") is not None:
            body["prior_interactions"] = args["prior_interactions"]
        return _request(ZJEV_URL, "/v1/outreach/evaluate", method="POST", body=body, headers=_zjev_headers())
    if name == "zjev_target_plan":
        body = {key: args[key] for key in ("offer", "geography", "company_terms", "buyer_titles", "priority_signals") if args.get(key) is not None}
        return _request(ZJEV_URL, "/v1/outreach/target-plan", method="POST", body=body, headers=_zjev_headers())
    raise ValueError(f"Unknown tool: {name}")


def _validate_tool_args(name: str, args: Any) -> None:
    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be an object")

    required = {
        "zrag_search": ("query",),
        "zrag_source": ("source_id",),
        "zjev_job_fit": ("cv", "job_description"),
        "zjev_outreach_evaluate": ("target_profile", "linkedin_activity", "offer", "proof_assets"),
        "zjev_target_plan": ("offer",),
    }
    if name not in required:
        raise ValueError(f"Unknown tool: {name}")
    missing = [key for key in required[name] if key not in args]
    if missing:
        raise ValueError(f"Missing required argument(s): {', '.join(missing)}")

    string_fields = {
        "zrag_search": ("query", "collection"),
        "zrag_source": ("source_id", "collection"),
        "zjev_outreach_evaluate": ("target_profile", "linkedin_activity", "prior_interactions", "offer"),
        "zjev_target_plan": ("offer", "geography"),
    }.get(name, ())
    for field in string_fields:
        if field in args and not isinstance(args[field], str):
            raise ValueError(f"{field} must be a string")
    if name == "zrag_search" and not args["query"].strip():
        raise ValueError("query must not be empty")
    if name == "zrag_source" and not args["source_id"].strip():
        raise ValueError("source_id must not be empty")

    if name in ("zrag_search", "zrag_source") and "limit" in args:
        limit = args["limit"]
        maximum = 10 if name == "zrag_search" else 100
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= maximum:
            raise ValueError(f"limit must be an integer from 1 to {maximum}")
    if name == "zrag_source" and "offset" in args:
        offset = args["offset"]
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")
    if name == "zjev_outreach_evaluate":
        if not isinstance(args["proof_assets"], list) or any(not isinstance(x, str) for x in args["proof_assets"]):
            raise ValueError("proof_assets must be an array of strings")
    if name == "zjev_target_plan":
        for field in ("company_terms", "buyer_titles", "priority_signals"):
            if field in args and (not isinstance(args[field], list) or any(not isinstance(x, str) for x in args[field])):
                raise ValueError(f"{field} must be an array of strings")


def _reply(request_id: Any, result: Any) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _reply_error(request_id: Any, code: int, message: str) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            _reply_error(None, -32700, f"Parse error: {exc.msg}")
            continue
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
            _reply_error(request.get("id") if isinstance(request, dict) else None, -32600, "Invalid Request")
            continue
        method = request.get("method")
        request_id = request.get("id")
        if request_id is None:
            # JSON-RPC notifications never receive a response.
            continue
        if method == "initialize":
            _reply(request_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "zjev-zrag", "version": "1.0.0"}})
        elif method in ("notifications/initialized", "notifications/cancelled", "ping"):
            _reply(request_id, {})
        elif method == "tools/list":
            _reply(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            try:
                params = request.get("params", {})
                if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                    raise ValueError("tools/call requires a tool name")
                _reply(request_id, _json_response(_call(params["name"], params.get("arguments", {}))))
            except Exception as exc:
                _reply(request_id, _error(str(exc)))
        else:
            _reply_error(request_id, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    main()
