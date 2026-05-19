"""摘要生成器——将原始采集数据格式化为结构化摘要 (由 Agent LLM 实际生成内容，此处负责格式编排)"""

import json
import os
from datetime import date
from typing import Optional

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
DIGEST_DIR = os.path.join(OUTPUT_DIR, "digests")


def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(DIGEST_DIR, exist_ok=True)


def load_raw_data(target_date: Optional[str] = None) -> dict:
    """加载当天的原始采集数据"""
    ensure_dirs()
    if target_date is None:
        target_date = date.today().isoformat()

    # 合并所有数据源
    combined = {"date": target_date, "articles": [], "sources": {}}

    if os.path.exists(RAW_DIR):
        for fname in sorted(os.listdir(RAW_DIR)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(RAW_DIR, fname)
            with open(fpath, "r") as f:
                data = json.load(f)
            if isinstance(data, dict) and "articles" in data:
                combined["articles"].extend(data["articles"])
                src = data.get("source", fname.replace(".json", ""))
                combined["sources"][src] = len(data["articles"])
            elif isinstance(data, list):
                combined["articles"].extend(data)

    # 去掉重复的 title
    seen_titles = set()
    unique = []
    for a in combined["articles"]:
        t = a.get("title", "")
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique.append(a)
    combined["articles"] = unique

    return combined


def format_for_llm(data: dict) -> str:
    """将数据格式化为 LLM 输入的文本"""
    lines = [
        f"## {data['date']} 宏观资讯汇总",
        f"共 {len(data['articles'])} 条资讯",
        "---",
    ]
    for src, count in data.get("sources", {}).items():
        lines.append(f"- {src}: {count}条")

    lines.append("\n---\n## 详细资讯列表\n")
    for i, article in enumerate(data["articles"], 1):
        title = article.get("title", "无标题")
        src = article.get("source", "未知")
        url = article.get("article_url") or article.get("url", "")
        content = article.get("content", "")[:300]

        lines.append(f"### {i}. [{title}]({url})")
        lines.append(f"来源: {src}")
        if content:
            lines.append(f"> {content}")
        lines.append("")

    return "\n".join(lines)


def save_digest(date_str: str, content: str):
    """保存摘要到文件"""
    ensure_dirs()
    path = os.path.join(DIGEST_DIR, f"digest_{date_str}.md")
    with open(path, "w") as f:
        f.write(content)
    return path
