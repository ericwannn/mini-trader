---
name: minitrader-web
description: >-
  Manages MiniTrader FastAPI web UI (start/stop/restart/status, frontend pages).
  Use when the user asks to start server, port 8000, frontend, or web dashboard.
---

# MiniTrader Web 服务

## 后台管理（推荐）

```bash
./scripts/minitrader-server.sh start
./scripts/minitrader-server.sh status
./scripts/minitrader-server.sh restart
./scripts/minitrader-server.sh stop
```

等价 CLI：`uv run minitrader serve start|stop|restart|status`

## 前台调试

```bash
uv run minitrader frontend
```

## 配置

| 变量 | 默认 |
|------|------|
| `MINITRADER_SERVER_HOST` | `0.0.0.0` |
| `MINITRADER_SERVER_PORT` | `8000` |

- PID：`output/minitrader-server.pid`
- 日志：`output/minitrader-server.log`
- 健康检查：`GET /health`

## 主要路由

| 路径 | 功能 |
|------|------|
| `/` | 摘要时间线 |
| `/digest/<date>` | 当日摘要 + 议题 + 文章 |
| `/article/<id>` | 站内阅读文章 |
| `/limitup` | 涨停复盘 |
| `/search` | 全文搜索 |

## 代码位置

- `src/minitrader/frontend/app.py`
- 进程管理：`src/minitrader/service.py`
