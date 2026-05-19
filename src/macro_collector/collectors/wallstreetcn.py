"""华尔街见闻快讯采集器"""

from __future__ import annotations

from typing import Optional

from macro_collector.collectors.base import BaseCollector
from macro_collector.models import Article
from macro_collector.utils import make_session


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
                articles.append(
                    Article(
                        title=item.get("title", "") or (item.get("content_text", "") or "")[:60],
                        account="华尔街见闻",
                        keyword_found="global-channel",
                        url=f"https://wallstreetcn.com/live/global/{item.get('id', '')}",
                        content=item.get("content_text", ""),
                        publish_time=item.get("display_time", ""),
                        source="wallstreetcn",
                    )
                )
            return articles
        except Exception as e:
            print(f"  ⚠️ 华尔街见闻采集失败: {e}")
            return []
