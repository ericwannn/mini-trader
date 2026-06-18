---
name: minitrader-collect
description: Use when collecting macro news, running minitrader collect, fixing WeChat/Sogou/Jin10/Wall Street CN/Sina collectors, or adding a new data source.
---

# MiniTrader 资讯采集

## 命令

```bash
cd <repo_root> && unset VIRTUAL_ENV
uv run minitrader collect
uv run minitrader collect --keywords "黄金 原油" --per-keyword 4 --max-total 25
```

## 输出

| 目标 | 路径 |
|------|------|
| 原始 JSON | `output/raw/raw_YYYY-MM-DD.json` |
| 文章库 | `minitrader.db` → `articles` |

## 采集源

| 源 | 模块 | 注意 |
|----|------|------|
| 搜狗微信 | `collectors/wechat.py` | 验证码→跳过；`MINITRADER_WECHAT_COOKIE` / `PROXY`；`ENABLED=0` 可关 |
| 华尔街见闻 | `collectors/wallstreetcn.py` | URL 用 API `uri` → `/livenews/{id}`，**勿** `/live/global/` |
| 金十 | `collectors/jin10.py` | 详情页 `/detail/...`；列表 URL 可能重复，入库时加 fragment |
| 新浪 | `collectors/sina.py` | 滚动快讯 |

注册表：`collectors/__init__.py` → `ALL_COLLECTORS`。CLI：`cli.py` → `do_collect`。入库：`db/sync.py` → `persist_articles`。

## 环境变量

`MINITRADER_WECHAT_ENABLED` / `PROXY` / `COOKIE`（见 `.env.example`）

## 常见错误

| 症状 | 处理 |
|------|------|
| 微信 0 条 | 验证码或 Cookie 失效；配代理/Cookie 或关微信源 |
| 见闻链接 404 | 检查是否仍生成 `/live/global/` |
| 金十多条同 URL | `sync._normalize_url` 已按标题 hash 区分 |
