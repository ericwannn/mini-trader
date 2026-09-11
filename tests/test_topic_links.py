import tempfile
import unittest
from pathlib import Path

from minitrader.db import get_topics_by_date, init_db, store_article, store_topics
from minitrader.db import models as db_models
from minitrader.models import Article
from minitrader.models.digest import extract_topics_from_articles


class TopicLinksTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_db = db_models.DB_PATH
        db_models.DB_PATH = str(Path(self._tmpdir.name) / "test.db")
        init_db()

    def tearDown(self) -> None:
        db_models.DB_PATH = self._orig_db
        self._tmpdir.cleanup()

    def test_lookup_article_id_by_title_and_date(self) -> None:
        store_article(
            url="https://weixin.sogou.com/link?url=expired",
            title="中东冲突全面冲击市场!黄金、原油、大宗商品行情复盘与后市预判",
            source="微信公众号",
            content="正文",
            published_at="",
        )
        aid = db_models.lookup_article_id(
            "中东冲突全面冲击市场!黄金、原油、大宗商品行情复盘与后市预判",
            "https://weixin.sogou.com/link?url=expired",
            "2026-05-21",
        )
        self.assertEqual(aid, 1)

    def test_topics_enriched_with_article_id(self) -> None:
        url = "https://weixin.sogou.com/link?url=expired-token"
        store_article(
            url=url,
            title="黄金走强",
            source="微信公众号",
            content="黄金看多",
            published_at="",
        )
        art = Article(
            title="黄金走强",
            account="测试号",
            keyword_found="黄金",
            url=url,
            content="黄金看多",
            source="sogou_wechat",
        )
        rows = extract_topics_from_articles([art], "2026-05-21")
        self.assertTrue(rows)
        import json

        rel = json.loads(rows[0]["related_articles"])
        self.assertEqual(rel[0].get("article_id"), 1)

        store_topics("2026-05-21", rows)
        loaded = get_topics_by_date("2026-05-21")
        self.assertEqual(loaded[0]["related_articles_list"][0]["article_id"], 1)


if __name__ == "__main__":
    unittest.main()
