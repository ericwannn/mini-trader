---
name: minitrader-digest
description: Use when generating daily digest Markdown, structured topics, direction judgement bugs, LLM or DeepSeek digest, or broken digest/topic links in the frontend.
---

# MiniTrader 摘要与议题

## 命令

```bash
uv run minitrader digest --date YYYY-MM-DD          # 规则引擎（默认）
uv run minitrader digest --date YYYY-MM-DD --llm    # OpenAI 兼容 API
uv run minitrader digest-llm --date YYYY-MM-DD
```

前置：`output/raw/raw_<date>.json`（先 `collect`）。LLM 需 `MINITRADER_LLM_API_KEY` + `MINITRADER_LLM_BASE_URL`（DeepSeek 见 README）。

## 输出

| 目标 | 路径 |
|------|------|
| Markdown | `output/digests/digest_<date>.md` |
| 摘要行 | `digests` 表 |
| 结构化议题 | `topics` 表（`actor`/`viewpoint`/`instruments`/`direction`/`forecast_cycle`/`logic`） |

## 核心代码

| 职责 | 位置 |
|------|------|
| 规则 Markdown | `models/digest.py` → `generate_digest_markdown` |
| 议题行 | `extract_topics_from_articles` |
| 方向/主体/标的 | `build_article_insight`, `_direction_judgement`, `_extract_actor` |
| 标题链接单行化 | `utils/markdown_text.py` → `make_markdown_header_link` |
| 议题站内链接 | `db/models.py` → `lookup_article_id`（搜狗外链易过期） |
| LLM | `digest/llm.py` |

## 方向判断规则（易踩坑）

- **主体**：机构/标题前缀；**排除**金十、华尔街见闻、ETF日报 等采集源/栏目名
- **标的**：标题优先（如光通信/通信ETF），勿被正文大盘指数带成仅「A股」
- **方向**：标题有推荐/景气词 + 正文仅为沪指涨跌复盘 → **以标题为准**（避免 ETF日报 被判看空）
- 无主体时核心观点省略主语，写「对 XX 持看多/看空…」

## 测试

```bash
uv run python -m unittest tests.test_topics tests.test_insight tests.test_markdown_text tests.test_topic_links -v
```

## 常见错误

| 症状 | 处理 |
|------|------|
| 议题标题显示原始 `[...](url)` | 标题含换行；`normalize_digest_markdown` / 重跑 digest |
| 搜狗微信链接 404 | 议题应链 `/article/{id}`；`get_topics_by_date` 会 enrich |
| 方向全是中性/反了 | 查 `_direction_judgement`；加用例到 `test_insight` |
| 改完议题未更新 | 重跑 `digest --date` 写库 |
