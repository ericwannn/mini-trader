#!/usr/bin/env bash
# 安装 macro-collector 包及依赖（editable）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

unset VIRTUAL_ENV

echo "=== 安装 macro-collector ==="
uv sync

if [[ ! -f .env ]] && [[ -f .env.example ]]; then
  cp .env.example .env
  echo "已从 .env.example 创建 .env，请按需修改配置"
fi

mkdir -p output/raw output/digests

echo ""
echo "安装完成。可用命令:"
echo "  uv run macro-collector --help"
echo "  uv run macro-collector serve start"
echo "  ./scripts/macro-server.sh status"
