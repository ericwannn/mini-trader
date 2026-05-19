#!/usr/bin/env bash
# macro-collector 统一入口（采集 / 摘要 / 服务管理等）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

unset VIRTUAL_ENV
exec uv run macro-collector "$@"
