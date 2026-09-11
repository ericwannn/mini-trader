"""华尔街见闻快讯采集器"""

from __future__ import annotations

from typing import Optional

from minitrader.collectors.base import BaseCollector
from minitrader.models import Article
from minitrader.utils import make_session
from minitrader.utils.markdown_text import sanitize_title_text


def wallstreetcn_live_url(item: dict) -> str:
    """快讯详情页 URL（API 的 uri 字段为准，勿用已失效的 /live/global/ 路径）。"""
    uri = (item.get("uri") or "").strip()
    if uri.startswith("http"):
        return uri
    live_id = item.get("id")
    if live_id is not None:
        return f"https://wallstreetcn.com/livenews/{live_id}"
    return ""


class WallStreetCnCollector(BaseCollector):
    """华尔街见闻快讯采集"""

    @property
    def source_name(self) -> str:
        return "华尔街见闻"

    def __init__(self) -> None:
        self.session = make_session()

    def fetch(self, max_items: Optional[int] = None) -> list[Article]:
        """采集快讯"""
        limit = max_items if max_items is not None else 30
        url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"
        try:
            r = self.session.get(url, timeout=15)
            data = r.json()
            articles = []
            for item in data.get("data", {}).get("items", [])[:limit]:
                raw_title = item.get("title", "") or (item.get("content_text", "") or "")
                title = sanitize_title_text(raw_title, max_len=80)
                articles.append(
                    Article(
                        title=title,
                        account="华尔街见闻",
                        keyword_found="global-channel",
                        url=wallstreetcn_live_url(item),
                        content=item.get("content_text", ""),
                        publish_time=item.get("display_time", ""),
                        source="wallstreetcn",
                    )
                )
            return articles
        except Exception as e:
            print(f"  ⚠️ 华尔街见闻采集失败: {e}")
            return []
