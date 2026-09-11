---
name: minitrader-daily
description: Use when running the full daily pipeline, cron scheduling, scripts/collect.sh, or verifying end-to-end output after collect digest and limitup.
---

# MiniTrader 一日全流程

## 命令

```bash
cd <repo_root> && unset VIRTUAL_ENV
uv run minitrader all
```

顺序：`collect` → `digest`（规则引擎，非 LLM）→ `limitup`

## Cron

```bash
./scripts/collect.sh
# 日志：output/collect_YYYY-MM-DD.log
```

```cron
30 17 * * 1-5 cd /path/to/mini-trader && ./scripts/collect.sh
```

## 验收

```bash
ls output/raw/raw_$(date +%F).json
ls output/digests/digest_$(date +%F).md
sqlite3 minitrader.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM digests;"
./scripts/minitrader-server.sh start
# 浏览器：/digest/<date>/topics
```

## 子流程 Skill

| 步骤 | Skill |
|------|-------|
| 采集 | `minitrader-collect` |
| 摘要 | `minitrader-digest` |
| 涨停 | `minitrader-limitup` |
| 浏览 | `minitrader-web` |

入口索引：`minitrader`
