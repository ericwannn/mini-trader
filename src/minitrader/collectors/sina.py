"""新浪财经新闻采集器"""

from __future__ import annotations

from typing import Optional

from minitrader.collectors.base import BaseCollector
from minitrader.models import Article
from minitrader.utils import make_session


class SinaCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "新浪财经"

    def __init__(self) -> None:
        self.session = make_session()

    def fetch(self, max_items: Optional[int] = None) -> list[Article]:
        """采集新浪财经头条新闻"""
        limit = max_items if max_items is not None else 20
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1"
        try:
            r = self.session.get(url, timeout=15)
            data = r.json()
            articles = []
            for item in data.get("result", {}).get("data", [])[:limit]:
                url = item.get("url") or item.get("wapurl") or item.get("link") or ""
                articles.append(
                    Article(
                        title=item.get("title", ""),
                        account="新浪财经",
                        keyword_found="sina_roll",
                        url=url,
                        content=item.get("intro", ""),
                        publish_time=item.get("ctime", ""),
                        source="sina",
                    )
                )
            return articles
        except Exception as e:
            print(f"  ⚠️ 新浪财经采集失败: {e}")
            return []
