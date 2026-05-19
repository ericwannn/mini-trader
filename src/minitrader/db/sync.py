"""DB 同步辅助——把采集结果与摘要写入 SQLite。"""

from __future__ import annotations

import hashlib
from typing import Iterable, Optional

from minitrader.db import init_db, store_article, store_digest, store_topics
from minitrader.models import Article, friendly_source


def _normalize_url(article: Article) -> str:
    """对 URL 做最小处理，避免同源不同条目共享 URL 时彼此覆盖。

    例如金十快讯 Top 列表的多条会共用 `https://flash.jin10.com/`；
    此时附加一个基于标题的短哈希作为 fragment，让 UNIQUE 约束放行。
    """
    url = (article.url or "").strip()
    if not url:
        return ""
    if url.endswith("/") or url.endswith("/#") or "/detail/" not in url and url.count("/") <= 3:
        digest = hashlib.md5((article.title or "").encode("utf-8")).hexdigest()[:10]
        sep = "&" if "?" in url else "#"
        if sep == "#" and "#" in url:
            return url  # 已有 fragment 则保留
        return f"{url}{sep}t={digest}"
    return url


def persist_articles(articles: Iterable[Article]) -> tuple[int, int]:
    """将文章批量写入 SQLite，返回 (新增, 跳过) 计数。"""
    init_db()
    inserted = 0
    skipped = 0
    for a in articles:
        url = _normalize_url(a)
        if not url or not a.title:
            skipped += 1
            continue
        source_label = friendly_source(a.source)
        ok = store_article(
            url=url,
            title=a.title,
            source=source_label,
            content=a.content or "",
            published_at=a.publish_time or "",
        )
        if ok:
            inserted += 1
        else:
            skipped += 1
    return inserted, skipped


def persist_digest(target_date: str, markdown: str, raw_path: Optional[str] = None) -> None:
    """把摘要 Markdown 写入 digests 表，raw_data 记录原始 JSON 路径以便溯源。"""
    init_db()
    store_digest(target_date, markdown, raw_data=raw_path or "")


def persist_topics(target_date: str, topics: list[dict]) -> int:
    """将结构化议题写入 topics 表。"""
    init_db()
    if not topics:
        return 0
    return store_topics(target_date, topics)
