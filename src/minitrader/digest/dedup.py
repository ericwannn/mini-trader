"""URL 去重——对新采集的文章列表过滤掉已存在的文章"""

from __future__ import annotations

from minitrader.db.models import article_exists, article_exists_by_title


def dedup_articles(articles: list[dict]) -> tuple[list[dict], int]:
    """对文章列表去重，返回 ``(保留列表, 跳过条数)``。"""
    kept: list[dict] = []
    skipped = 0
    for article in articles:
        url = article.get("article_url") or article.get("url") or ""
        title = article.get("title", "")
        source = article.get("source", "")

        if url and article_exists(url):
            skipped += 1
            continue
        if title and source and article_exists_by_title(title, source):
            skipped += 1
            continue

        kept.append(article)

    return kept, skipped
