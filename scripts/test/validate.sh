#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_dir"

python3 -m pytest -q tests
python3 -m py_compile mcp/zjev_zrag_mcp.py mcp/zjev_zrag_memory_mcp.py
