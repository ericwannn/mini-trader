---
name: minitrader-limitup
description: >-
  Fetches A-share limit-up board data via akshare into MiniTrader SQLite, with
  theme heat stats. Use when the user asks for 涨停复盘, limitup, or akshare integration.
---

# MiniTrader 涨停复盘

## 前置

- 依赖 `akshare`（`uv sync` 已包含）
- **A 股交易日 15:00 后**数据较完整

## 命令

```bash
uv run minitrader limitup
```

或一日流程末尾自动执行：

```bash
uv run minitrader all
```

## 输出

- `minitrader.db` → `limitup_records`、`theme_heat`
- 前端 `/limitup` 页面展示

## 代码位置

- `src/minitrader/limitup/collector.py`
- akshare 接口：`stock_zt_pool_em`，日期格式 `YYYYMMDD`

## 注意

- 同日重复运行会提示 `already_collected` 并复用库内数据
- 非交易日可能返回 0 条，属正常
