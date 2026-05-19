---
name: minitrader-collect
description: >-
  Runs MiniTrader multi-source macro news collection (WeChat/Sogou, Wall Street CN,
  Jin10, Sina), deduplication, raw JSON output, and SQLite article persistence.
  Use when the user asks to collect news, run minitrader collect, fix collectors,
  or extend data sources.
---

# MiniTrader 资讯采集

## 前置

- 项目根目录执行 `uv sync` 或 `./scripts/install.sh`
- 可选 `.env`：`MINITRADER_WECHAT_*`（搜狗微信代理/Cookie/开关）

## 标准流程

```bash
cd <repo_root>
unset VIRTUAL_ENV
uv run minitrader collect
```

可选微信参数：

```bash
uv run minitrader collect --keywords "黄金 原油" --per-keyword 4 --max-total 25
```

## 输出

| 路径 | 说明 |
|------|------|
| `output/raw/raw_YYYY-MM-DD.json` | 当日原始 JSON |
| `minitrader.db` `articles` 表 | 去重入库 |

## 代码位置

- 采集器注册：`src/minitrader/collectors/__init__.py` → `ALL_COLLECTORS`
- CLI：`src/minitrader/cli.py` → `do_collect`
- 入库：`src/minitrader/db/sync.py` → `persist_articles`

## 约定

- Python 使用**绝对路径** import：`from minitrader.xxx import ...`，禁止 `from .xxx`
- 微信遇验证码会跳过该关键词；可配置 Cookie/代理或 `MINITRADER_WECHAT_ENABLED=0`
