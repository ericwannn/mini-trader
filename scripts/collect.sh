#!/usr/bin/env bash
# minitrader：采集多源资讯并生成本地 Markdown 摘要
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

DATE="$(date +%Y-%m-%d)"
LOG_FILE="$PROJECT_DIR/output/collect_${DATE}.log"

mkdir -p "$PROJECT_DIR/output"

echo "============================================"
echo " MiniTrader - $DATE"
echo "============================================"
echo ""

uv run minitrader all 2>&1 | tee "$LOG_FILE"

echo ""
echo "完成。日志: $LOG_FILE"
