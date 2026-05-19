"""金十数据快讯采集器

优先使用稳定的 ``https://www.jin10.com/flash_newest.js`` JSON 接口（实测一次返回 50 条
最新快讯）；该接口失败时再回退到 ``flash.jin10.com`` HTML 解析。
"""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Optional

from minitrader.collectors.base import BaseCollector
from minitrader.models import Article
from minitrader.utils import make_session

_FLASH_NEWEST_URL = "https://www.jin10.com/flash_newest.js"
_FLASH_HOMEPAGE = "https://flash.jin10.com/"


class Jin10Collector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "金十数据"

    def __init__(self) -> None:
        self.session = make_session()

    # ── 主路径：flash_newest.js JSON ─────────────────────

    def _fetch_flash_newest(self) -> list[dict]:
        headers = {"Referer": "https://www.jin10.com/", "User-Agent": self.session.headers.get("User-Agent", "")}
        try:
            r = self.session.get(_FLASH_NEWEST_URL, headers=headers, timeout=15)
        except Exception as e:
            print(f"  ⚠️ flash_newest 请求失败: {e}")
            return []
        if r.status_code != 200:
            print(f"  ⚠️ flash_newest HTTP {r.status_code}")
            return []
        text = r.text.strip()
        m = re.match(r"var\s+\w+\s*=\s*(\[.*\])\s*;?\s*$", text, re.DOTALL)
        if not m:
            return []
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError as e:
            print(f"  ⚠️ flash_newest JSON 解析失败: {e}")
            return []

    @staticmethod
    def _flash_item_to_article(item: dict) -> Optional[Article]:
        fid = str(item.get("id") or "").strip()
        data = item.get("data") or {}
        itype = item.get("type", 0)
        title = (data.get("title") or "").strip()
        content_raw = (data.get("content") or "").strip()
        content = unescape(re.sub(r"<[^>]+>", "", content_raw)).strip()
        if not title:
            title = content[:60]
        if not (title or content) or not fid:
            return None
        if itype == 2 and data.get("link"):
            url = str(data["link"])
        else:
            url = f"https://flash.jin10.com/detail/{fid}"
        return Article(
            title=title[:120],
            account="金十数据",
            keyword_found="jin10_flash",
            url=url,
            content=content or title,
            publish_time=str(item.get("time", "")),
            source="jin10",
        )

    # ── 回退路径：HTML 解析 ─────────────────────────────

    def _fetch_with_encoding(self, url: str, timeout: int = 15) -> str:
        r = self.session.get(url, timeout=timeout)
        r.encoding = "utf-8"
        return r.text

    def _fetch_html_fallback(self, limit: int) -> list[Article]:
        try:
            html = self._fetch_with_encoding(_FLASH_HOMEPAGE)
        except Exception as e:
            print(f"  ⚠️ flash 首页请求失败: {e}")
            return []

        articles: list[Article] = []
        seen: set[str] = set()

        items = re.findall(
            r'flash-top-list__item[^>]*>.*?<div[^>]*>\d+</div>\s*<div[^>]*>(.*?)</div>',
            html, re.DOTALL,
        )
        for idx, item_html in enumerate(items[:5]):
            text = unescape(re.sub(r"<[^>]+>", "", item_html)).strip()
            key = text[:40]
            if not text or key in seen:
                continue
            seen.add(key)
            articles.append(Article(
                title=text[:80],
                account="金十数据",
                keyword_found="jin10_flash",
                url=f"https://flash.jin10.com/#top-{idx}",
                content=text,
                source="jin10",
            ))

        for fid in re.findall(r'/detail/(\d{18,})', html):
            if fid in seen:
                continue
            seen.add(fid)
            try:
                detail_html = self._fetch_with_encoding(
                    f"https://flash.jin10.com/detail/{fid}", timeout=8
                )
            except Exception:
                continue
            m = re.search(r'"content":"((?:[^"\\]|\\.)*)"', detail_html)
            if not m:
                continue
            content = m.group(1).replace('\\"', '"').replace("\\n", "\n")
            articles.append(Article(
                title=content[:80],
                account="金十数据",
                keyword_found="jin10_flash",
                url=f"https://flash.jin10.com/detail/{fid}",
                content=content,
                source="jin10",
            ))
            if len(articles) >= limit:
                break

        return articles

    # ── 对外接口 ───────────────────────────────────────

    def fetch(self, max_items: Optional[int] = None) -> list[Article]:
        limit = max_items if max_items is not None else 30

        items = self._fetch_flash_newest()
        if items:
            articles: list[Article] = []
            seen: set[str] = set()
            for item in items:
                article = self._flash_item_to_article(item)
                if not article:
                    continue
                key = article.url or article.title[:40]
                if key in seen:
                    continue
                seen.add(key)
                articles.append(article)
                if len(articles) >= limit:
                    break
            if articles:
                return articles

        return self._fetch_html_fallback(limit)
