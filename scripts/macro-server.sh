#!/usr/bin/env bash
# Macro Collector Web 后端管理
# 用法: ./scripts/macro-server.sh {start|stop|restart|status} [额外参数传给 CLI]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

unset VIRTUAL_ENV

CMD="${1:-status}"
shift || true

case "$CMD" in
  start|stop|restart|status)
    exec uv run macro-collector serve "$CMD" "$@"
    ;;
  -h|--help|help)
    cat <<'EOF'
用法: ./scripts/macro-server.sh <command> [options]

  start     后台启动 FastAPI（默认 http://localhost:8000）
  stop      停止后台服务
  restart   重启后台服务
  status    查看 PID / 健康检查 / 日志路径

环境变量（可写入 .env）:
  MACRO_SERVER_HOST   监听地址，默认 0.0.0.0
  MACRO_SERVER_PORT   端口，默认 8000

示例:
  ./scripts/macro-server.sh start
  ./scripts/macro-server.sh start --port 8765
  ./scripts/macro-server.sh status
EOF
    ;;
  *)
    echo "未知命令: $CMD（可用: start | stop | restart | status）" >&2
    exit 1
    ;;
esac
