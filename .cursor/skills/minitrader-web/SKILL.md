---
name: minitrader-web
description: Use when starting or debugging the FastAPI UI, port 8000 conflicts, Internal Server Error on homepage, Tailscale remote access, or digest/limitup frontend routes.
---

# MiniTrader Web 服务

## 启停

```bash
./scripts/minitrader-server.sh start|status|restart|stop
# 等价：uv run minitrader serve start|status|...
uv run minitrader frontend   # 前台调试
```

| 项 | 值 |
|----|-----|
| 默认 | `0.0.0.0:8000` |
| PID | `output/minitrader-server.pid` |
| 日志 | `output/minitrader-server.log` |
| 健康 | `GET /health` → `{"service":"minitrader"}` |

`MINITRADER_SERVER_HOST` / `PORT`。`serve status` 在绑定 `0.0.0.0` 时可能打印 Tailscale IP。

## 路由

| 路径 | 页面 |
|------|------|
| `/` | 摘要时间线（链到最近摘要） |
| `/digest/<date>/topics` | 结构化议题 |
| `/digest/<date>/summary` | 宏观摘要 Markdown + 参考文章 |
| `/digest/<date>/limitup` | 当日涨停分析 |
| `/digest/<date>` | 302 → topics |
| `/article/<id>` | 站内读文 |
| `/limitup` | 涨停复盘（选日期） |
| `/search` | 搜索 |

顶栏：有 `focus_date` 时显示「结构化议题 / 宏观摘要 / 涨停分析」三 Tab；首页用最近摘要日期填充链接。

模板：`frontend/templates/`（`base.html` + `_nav.html`）。Markdown 渲染：`frontend/markdown_render.py`。

## 常见错误

| 症状 | 处理 |
|------|------|
| 500 / 旧服务 | `lsof -i :8000`；杀掉 `macro_collector` 进程；`serve` 要求 health `service=minitrader` |
| 端口占用 | `./scripts/minitrader-server.sh restart` |
| 手机访问 | Tailscale + `http://100.x.x.x:8000`（无登录，勿 Funnel） |

代码：`frontend/app.py`、`service.py`。
