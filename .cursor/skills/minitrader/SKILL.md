---
name: minitrader
description: Use when working in the mini-trader repo without a clear subcommand, or when the user mentions MiniTrader, daily_digest, macro digest, or A-share trading assistant workflows.
---

# MiniTrader 总览

个人交易辅助：`minitrader` 包，数据在 `output/` + `minitrader.db`。

## 选哪个 Skill

| 用户意图 / 症状 | Skill |
|----------------|-------|
| 采集新闻、修采集器、微信/金十/见闻 | `minitrader-collect` |
| 生成摘要、议题、方向判断、LLM/DeepSeek | `minitrader-digest` |
| 涨停复盘、akshare、题材热度 | `minitrader-limitup` |
| 启动 Web、8000 端口、前端页面 | `minitrader-web` |
| `all`、cron、一日流水线 | `minitrader-daily` |

## 快速命令

```bash
cd <repo_root> && unset VIRTUAL_ENV
uv run minitrader collect | digest --date YYYY-MM-DD | limitup | all
./scripts/minitrader-server.sh start
```

## 硬性约定

- Python import：`from minitrader.xxx import ...`（禁止 `from .xxx`）
- 项目根执行 `uv run`；勿混用外部 `VIRTUAL_ENV`
- `.env` / `output/` / `minitrader.db` 不入库

## 代码地图

| 模块 | 路径 |
|------|------|
| CLI | `src/minitrader/cli.py` |
| 摘要规则引擎 | `src/minitrader/models/digest.py` |
| LLM 摘要 | `src/minitrader/digest/llm.py` |
| SQLite | `src/minitrader/db/` |
| 前端 | `src/minitrader/frontend/app.py` |
| 进程管理 | `src/minitrader/service.py` |

## 测试

```bash
uv run python -m unittest discover -s tests -v
```

修改 `digest.py` 方向/议题逻辑后至少跑 `tests.test_topics`、`tests.test_insight`。
