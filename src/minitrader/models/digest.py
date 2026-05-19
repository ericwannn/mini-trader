"""摘要生成模块 — 基于原始文章数据，生成结构化 Markdown 日报"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Optional

from minitrader.models import Article, friendly_source


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
DIGEST_DIR = os.path.join(OUTPUT_DIR, "digests")

TOPIC_SPECS: list[tuple[str, tuple[str, ...]]] = [
    ("黄金/贵金属", ("黄金", "金价", "贵金属", "避险")),
    ("原油/能源", ("原油", "石油", "能源", "OPEC", "霍尔木兹")),
    ("A股/港股", ("A股", "港股", "沪深", "上证", "创业板")),
    ("美股", ("美股", "标普", "纳斯达克", "道指")),
    ("外汇/汇率", ("美元", "人民币", "汇率", "外汇", "美联储")),
    ("债券/利率", ("债券", "利率", "国债", "收益率")),
    ("宏观政策", ("政策", "GDP", "经济数据", "十五五", "改革")),
    ("大宗商品", ("大宗商品", "铜", "铁矿石", "农产品")),
]

_OTHER_TOPIC = "其他宏观资讯"

_BULL_KEYWORDS: tuple[str, ...] = (
    "看多",
    "看涨",
    "利多",
    "利好",
    "超配",
    "增持",
    "买入",
    "上调",
    "上行",
    "上涨",
    "大涨",
    "飙升",
    "走强",
    "反弹",
    "回升",
    "拉升",
    "突破",
    "创新高",
    "扩张",
    "回暖",
    "修复",
    "配置价值",
    "机会",
    "推荐",
)
_BEAR_KEYWORDS: tuple[str, ...] = (
    "看空",
    "看跌",
    "利空",
    "偏空",
    "减持",
    "卖出",
    "下调",
    "下行",
    "下跌",
    "大跌",
    "暴跌",
    "走弱",
    "下挫",
    "回落",
    "回调",
    "跌破",
    "创新低",
    "萎缩",
    "收缩",
    "承压",
    "拖累",
    "冲击",
    "谨慎",
)
# 快讯/盘面常用表述（单次计分，避免「涨」「跌」子串重复叠加）
_BULL_MOVE_RE = re.compile(
    r"(?:收涨|领涨|上涨|大涨|涨幅|走高|升至|涨超|涨停|涨\d|涨\s*[\d.]+%)"
)
_BEAR_MOVE_RE = re.compile(
    r"(?:收跌|领跌|下跌|大跌|跌幅|走低|降至|跌超|跌停|跌\d|跌\s*[\d.]+%|跌幅达)"
)

_VARIETY_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("黄金", ("黄金", "COMEX金", "金价")),
    ("白银", ("白银",)),
    ("原油", ("原油", "布伦特", "WTI", "油价", "石油")),
    ("铜", ("铜", "LME铜")),
    ("铁矿石", ("铁矿石",)),
    ("A股", ("A股", "沪深300", "上证综指", "上证", "创业板")),
    ("港股", ("港股", "恒生")),
    ("美股", ("美股", "纳斯达克", "标普500", "道指")),
    ("美债", ("美债", "美国国债")),
    ("中债/国债", ("国债", "国开债", "利率债")),
    ("人民币/外汇", ("人民币", "汇率", "美元", "CNY", "CNH")),
    ("黄金ETF", ("黄金ETF",)),
]


def save_raw(articles: list[Article], target_date: Optional[str] = None) -> str:
    """保存原始文章数据为 JSON"""
    os.makedirs(RAW_DIR, exist_ok=True)
    today = target_date or datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(RAW_DIR, f"raw_{today}.json")
    with_content = sum(1 for a in articles if a.content)
    data = {
        "date": today,
        "total": len(articles),
        "with_content": with_content,
        "articles": [a.to_dict() for a in articles],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存: {path}")
    return path


def load_raw(target_date: str) -> list[Article]:
    """从 JSON 文件加载原始文章"""
    path = os.path.join(RAW_DIR, f"raw_{target_date}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到原始数据文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Article.from_dict(a) for a in data["articles"]]


def _article_text(a: Article, limit: int = 12000) -> str:
    return f"{a.title}\n{a.content or ''}"[:limit]


def _dedupe_articles(seq: list[Article]) -> list[Article]:
    seen: set[str] = set()
    out: list[Article] = []
    for a in seq:
        key = (a.url or "").strip() or f"{a.title}\0{a.account}"
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def _bucket_by_topics(articles: list[Article]) -> dict[str, list[Article]]:
    buckets: dict[str, list[Article]] = {name: [] for name, _ in TOPIC_SPECS}
    buckets[_OTHER_TOPIC] = []
    for a in articles:
        text = _article_text(a)
        matched = [name for name, kws in TOPIC_SPECS if any(kw in text for kw in kws)]
        if not matched:
            buckets[_OTHER_TOPIC].append(a)
        else:
            for name in matched:
                buckets[name].append(a)
    return buckets


def _extract_varieties(a: Article) -> str:
    text = _article_text(a, 8000)
    found: list[str] = []
    for label, patterns in _VARIETY_PATTERNS:
        if any(p in text for p in patterns) and label not in found:
            found.append(label)
    return "、".join(found) if found else "(未显式提取，见摘要)"


def _direction_scores(text: str) -> tuple[int, int]:
    """统计多空信号强度（关键词各计 1 分，盘面涨跌表述按命中次数计分）。"""
    bull = sum(1 for w in _BULL_KEYWORDS if w in text)
    bear = sum(1 for w in _BEAR_KEYWORDS if w in text)
    bull += len(_BULL_MOVE_RE.findall(text))
    bear += len(_BEAR_MOVE_RE.findall(text))
    return bull, bear


def _direction_judgement(a: Article) -> str:
    bull, bear = _direction_scores(_article_text(a, 8000))
    if bull > bear:
        return "看多"
    if bear > bull:
        return "看空"
    return "中性"


def _horizon(a: Article) -> str:
    text = _article_text(a, 4000)
    if any(x in text for x in ("短期", "短线", "周内", "近日", "1-3月")):
        return "短期(1-3月)"
    if any(x in text for x in ("长期", "战略", "1年+", "一年以上", "多年")):
        return "长期(1年+)"
    return "中期(3-12月)"


def _logic_chain(a: Article) -> str:
    body = (a.content or "").strip()
    if not body:
        return "1. 原文未提供可解析正文，建议点击链接阅读原文。"
    parts = re.split(r"[。！？\n]+", body)
    steps = [p.strip() for p in parts if len(p.strip()) > 12][:3]
    if not steps:
        chunk = body[:240].replace("\n", " ")
        return f"1. {chunk}"
    return "\n".join(f"{i + 1}. {steps[i]}" for i in range(len(steps)))


def _overview_paragraph(articles: list[Article], buckets: dict[str, list[Article]]) -> str:
    n = len(articles)
    counts = [
        (name, len(_dedupe_articles(buckets[name])))
        for name, _ in TOPIC_SPECS
        if buckets[name]
    ]
    counts.sort(key=lambda x: -x[1])
    top = [c[0] for c in counts[:3]]
    if not top:
        tail = len(buckets.get(_OTHER_TOPIC, []))
        if tail:
            return (
                f"本日共整理资讯 {n} 条；未命中预设关键词分组，已归入「{_OTHER_TOPIC}」。"
                " 建议结合标题与链接快速浏览。"
            )
        return f"本日无可用资讯条目（{n} 条）。"
    themes = "、".join(top)
    return (
        f"本日共整理 {n} 条资讯，覆盖核心议题包括：{themes}。"
        " 下文按议题归类摘录要点，每条均保留标题与可点击原文链接，便于复核。"
    )


def _format_article_block(a: Article) -> str:
    account = (a.account or "").strip() or friendly_source(a.source) or "未知来源"
    url = ((a.url or "").strip() or "#")
    summary_raw = (a.content or "").strip()
    summary = summary_raw[:200].replace("\n", " ") if summary_raw else "(无正文摘要)"
    title_md = f"[{a.title}]({url})" if url and url != "#" else a.title
    lines = [
        f"### {title_md}",
        f"- **来源**: {account} | [原文链接]({url})",
        f"- **内容摘要**: {summary}",
        f"- **涉及品种**: {_extract_varieties(a)}",
        f"- **方向判断**: {_direction_judgement(a)}",
        f"- **预测周期**: {_horizon(a)}",
        f"- **分析逻辑**: {_logic_chain(a)}",
    ]
    return "\n".join(lines)


def generate_digest_markdown(articles: list[Article], target_date: str) -> str:
    """按关键词议题归类，生成完整 Markdown 日报（含标题与原文链接）。"""
    buckets = _bucket_by_topics(articles)
    parts: list[str] = [
        f"# 每日宏观资产配置摘要 — {target_date}",
        "",
        "## 总体概述",
        _overview_paragraph(articles, buckets),
        "",
        "---",
        "",
    ]
    section_no = 0
    for topic_name, _ in TOPIC_SPECS:
        arts = _dedupe_articles(buckets[topic_name])
        if not arts:
            continue
        section_no += 1
        parts.append(f"## {section_no}. {topic_name}")
        parts.append("")
        for a in arts:
            parts.append(_format_article_block(a))
            parts.append("")
        parts.append("---")
        parts.append("")
    other = _dedupe_articles(buckets[_OTHER_TOPIC])
    if other:
        section_no += 1
        parts.append(f"## {section_no}. {_OTHER_TOPIC}")
        parts.append("")
        for a in other:
            parts.append(_format_article_block(a))
            parts.append("")
        parts.append("---")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def extract_topics_from_articles(
    articles: list[Article], target_date: str
) -> list[dict[str, str]]:
    """从文章列表提取结构化议题行（与 Markdown 摘要字段一致）。"""
    buckets = _bucket_by_topics(articles)
    records: list[dict[str, str]] = []

    def _append_for_topic(topic_name: str, arts: list[Article]) -> None:
        for a in _dedupe_articles(arts):
            related = json.dumps(
                [{"title": a.title, "url": (a.url or "").strip() or "#"}],
                ensure_ascii=False,
            )
            records.append(
                {
                    "digest_date": target_date,
                    "keyword": topic_name,
                    "instruments": _extract_varieties(a),
                    "direction": _direction_judgement(a),
                    "forecast_cycle": _horizon(a),
                    "logic": _logic_chain(a),
                    "related_articles": related,
                }
            )

    for topic_name, _ in TOPIC_SPECS:
        if buckets[topic_name]:
            _append_for_topic(topic_name, buckets[topic_name])
    if buckets[_OTHER_TOPIC]:
        _append_for_topic(_OTHER_TOPIC, buckets[_OTHER_TOPIC])
    return records


_ARTICLE_BLOCK_RE = re.compile(
    r"###\s*(?:"
    r"文章:\s*(?P<title>[^\n]+)"
    r"|\[(?P<title_link>[^\]]+)\]\([^)]+\)"
    r")\n"
    r"(?P<body>.*?)(?=\n###\s*(?:文章:|\[)|\n##\s|\Z)",
    re.DOTALL,
)
_FIELD_RE = {
    "instruments": re.compile(r"-\s*\*\*涉及品种\*\*:\s*(.+)", re.MULTILINE),
    "direction": re.compile(r"-\s*\*\*方向判断\*\*:\s*(.+)", re.MULTILINE),
    "forecast_cycle": re.compile(r"-\s*\*\*预测周期\*\*:\s*(.+)", re.MULTILINE),
    "logic": re.compile(r"-\s*\*\*分析逻辑\*\*:\s*((?:.|\n)*?)(?=\n-\s*\*\*|\Z)", re.MULTILINE),
}
_LINK_RE = re.compile(r"\[原文链接\]\(([^)]+)\)")


def parse_topics_from_markdown(markdown: str, target_date: str) -> list[dict[str, str]]:
    """从已生成的 Markdown 摘要解析 topics（LLM 或历史文件回灌）。"""
    records: list[dict[str, str]] = []
    sections = re.split(r"\n##\s+\d+\.\s+", markdown)
    if len(sections) <= 1:
        for m in _ARTICLE_BLOCK_RE.finditer(markdown):
            records.append(_topic_row_from_block(m, target_date, "综合"))
        return records

    for section in sections[1:]:
        lines = section.split("\n", 1)
        keyword = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        for m in _ARTICLE_BLOCK_RE.finditer(body):
            records.append(_topic_row_from_block(m, target_date, keyword))
    return records


def _topic_row_from_block(
    match: re.Match[str], target_date: str, keyword: str
) -> dict[str, str]:
    title = (match.group("title") or match.group("title_link") or "").strip()
    body = match.group("body")
    url_m = _LINK_RE.search(body)
    url = url_m.group(1).strip() if url_m else "#"
    row: dict[str, str] = {
        "digest_date": target_date,
        "keyword": keyword,
        "instruments": "",
        "direction": "",
        "forecast_cycle": "",
        "logic": "",
        "related_articles": json.dumps(
            [{"title": title, "url": url}], ensure_ascii=False
        ),
    }
    for field, pattern in _FIELD_RE.items():
        fm = pattern.search(body)
        if fm:
            row[field] = fm.group(1).strip()
    return row


def save_digest(markdown: str, target_date: str) -> str:
    os.makedirs(DIGEST_DIR, exist_ok=True)
    path = os.path.join(DIGEST_DIR, f"digest_{target_date}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"摘要 Markdown 已保存: {path}")
    return path


def generate_intro_prompt(articles: list[Article], today: str) -> str:
    """构造 AI 分析所需的 Prompt"""

    # 筛选有正文的文章
    valid = [a for a in articles if a.content and len(a.content) > 100]

    articles_text = ""
    for i, a in enumerate(valid, 1):
        articles_text += f"""
### 文章{i}
- 标题: {a.title}
- 公众号: {a.account}
- 原文链接: {a.url}
- 关键词来源: {a.keyword_found}
- 正文摘要: {a.content[:800]}
"""

    prompt = f"""你是一个专业的宏观资产配置分析师。请基于以下{len(valid)}篇来自微信公众号的宏观分析文章，生成一份结构化日报。

日期: {today}

要求:
1. 识别出 3-6 个核心议题（跨文章的共同主题）
2. 每个议题必须包含以下字段：
   - **关键词**: 3-6 个关键词
   - **涉及品种**: 所有可交易品种（股票指数、商品、货币、债券、板块等）
   - **方向判断**: 明确的看多/看空判断
   - **预测周期**: 短期(1-3月)、中期(3-12月)、长期(1年+)
   - **分析逻辑链条**: 分步骤列出逻辑推演过程（>=3 步）
   - **来源文章**: 每篇文章的标题和原文链接，方便读者点击查看
3. 格式使用 Markdown 的 ### 三级标题

{articles_text}

请确保：
- 逻辑链条清晰、具体、有层次
- 保留不同来源的差异化观点
- 来源文章附上完整标题和可点击链接
- 如果没有足够信息支撑某个议题，不要强行凑数"""
    return prompt
