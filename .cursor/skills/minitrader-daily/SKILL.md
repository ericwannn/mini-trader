---
name: minitrader-daily
description: >-
  Runs the full MiniTrader daily pipeline: collect, digest, limitup, DB sync; cron
  via scripts/collect.sh. Use when the user asks for daily workflow, cron, or
  minitrader all.
---

# MiniTrader 一日全流程

## 标准命令

```bash
cd <repo_root>
unset VIRTUAL_ENV
uv run minitrader all
```

顺序：`collect` → `digest`（规则引擎）→ `limitup`（akshare 入库）

## Cron

```bash
./scripts/collect.sh
# 日志：output/collect_YYYY-MM-DD.log
```

```cron
30 17 * * 1-5 cd /path/to/mini-trader && ./scripts/collect.sh
```

## 验证

```bash
ls output/raw/raw_$(date +%F).json
ls output/digests/digest_$(date +%F).md
sqlite3 minitrader.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM digests;"
./scripts/minitrader-server.sh start
```

## 相关 Skill

- 仅采集 → `minitrader-collect`
- 仅摘要 / LLM → `minitrader-digest`
- 仅涨停 → `minitrader-limitup`
- Web → `minitrader-web`
