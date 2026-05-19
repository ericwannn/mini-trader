---
name: minitrader-digest
description: >-
  Generates MiniTrader daily macro digest Markdown from raw JSON (rule engine or
  LLM via OpenAI-compatible API including DeepSeek), writes topics to SQLite.
  Use when the user asks for digest, summary, LLM digest, or direction/topic fixes.
---

# MiniTrader 摘要生成

## 前置

- 已有 `output/raw/raw_<date>.json`（先 `minitrader collect`）
- LLM 模式需 `.env` 中 `MINITRADER_LLM_API_KEY` + `MINITRADER_LLM_BASE_URL`

## 规则引擎（默认）

```bash
uv run minitrader digest --date YYYY-MM-DD
```

## LLM（OpenAI 兼容 / DeepSeek）

```bash
# .env 示例（DeepSeek）
# MINITRADER_LLM_API_KEY=sk-...
# MINITRADER_LLM_BASE_URL=https://api.deepseek.com
# MINITRADER_LLM_MODEL=deepseek-chat

uv run minitrader digest --date YYYY-MM-DD --llm
# 或
uv run minitrader digest-llm --date YYYY-MM-DD
```

无 API Key 时 CLI 会 exit 1 并提示配置。

## 输出

| 路径 | 说明 |
|------|------|
| `output/digests/digest_<date>.md` | Markdown 日报 |
| `minitrader.db` `digests` / `topics` | 摘要与结构化议题 |

## 代码位置

- 规则摘要：`src/minitrader/models/digest.py`（`generate_digest_markdown`、方向判断 `_direction_judgement`）
- LLM：`src/minitrader/digest/llm.py`
- CLI：`src/minitrader/cli.py` → `do_digest`

## 约定

- 修改方向判断时同步跑 `python -m unittest tests.test_topics`
- LLM 与规则引擎二选一；规则引擎不消耗 API
