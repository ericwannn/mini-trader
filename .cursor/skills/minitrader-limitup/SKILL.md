---
name: minitrader-limitup
description: Use when fetching A-share limit-up data, 涨停复盘, theme heat stats, akshare errors, or limitup page shows empty on a trading day.
---

# MiniTrader 涨停复盘

## 命令

```bash
uv run minitrader limitup
# 或一日流程末尾：uv run minitrader all
```

**交易日 15:00 后**数据较完整。非交易日 0 条正常。

## 输出

`minitrader.db` → `limitup_records`、`theme_heat`

| 字段 | 说明 |
|------|------|
| `themes` | akshare「所属行业」（原涨停原因字段已废弃） |
| `consecutive_days` | 连板数 |

代码：`limitup/collector.py`，接口 `akshare.stock_zt_pool_em`，日期 `YYYYMMDD`。同日重复运行提示 `already_collected`。

## 前端

- 全局：`/limitup`（日期下拉）
- 与摘要同日：`/digest/<date>/limitup`

## 常见错误

| 症状 | 处理 |
|------|------|
| 0 条 | 非交易日或未收盘；看 CLI 报错 |
| 题材显示截断 | 行业名来自东财，保留原样 |
