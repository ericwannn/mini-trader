import unittest

from minitrader.models import Article
from minitrader.models.digest import (
    _direction_judgement,
    _extract_actor,
    build_article_insight,
    generate_digest_markdown,
)


class InsightTestCase(unittest.TestCase):
    def test_actor_from_title_prefix(self) -> None:
        a = Article(
            title="美国银行调查：若美债大幅波动 30年期收益率或升至6%以上",
            account="华尔街见闻",
            keyword_found="",
            url="https://example.com/1",
            content="若美债收益率大幅波动，30年期或升至6%以上。",
            source="wallstreetcn",
        )
        self.assertEqual(_extract_actor(a), "美国银行调查")

    def test_flash_source_has_no_media_actor(self) -> None:
        a = Article(
            title="现货黄金短线走高",
            account="金十",
            keyword_found="",
            url="https://example.com/2",
            content="现货黄金短线走高，日内涨0.3%。",
            source="jin10",
        )
        self.assertEqual(_extract_actor(a), "")
        ins = build_article_insight(a)
        self.assertEqual(ins["actor"], "")
        self.assertNotIn("金十", ins["viewpoint"])

    def test_institution_from_body_over_media_account(self) -> None:
        a = Article(
            title="高盛上调黄金目标价",
            account="华尔街见闻",
            keyword_found="",
            url="https://example.com/3",
            content="高盛认为黄金仍有上行空间，维持看多。",
            source="wallstreetcn",
        )
        self.assertEqual(_extract_actor(a), "高盛")

    def test_etf_column_title_not_bearish_on_index_recap(self) -> None:
        a = Article(
            title="ETF日报：资本开支高增长铸就景气支撑，光通信板块景气度高企，关注通信ETF",
            account="新浪财经",
            keyword_found="",
            url="https://example.com/etf",
            content=(
                "市场全天冲高回落，沪指失守4100点。沪深两市成交额3.48万亿。"
                "截至收盘，沪指跌2.04%，深成指跌2.07%，创业板指跌2.35%。"
            ),
            source="sina",
        )
        self.assertEqual(_direction_judgement(a), "看多")
        ins = build_article_insight(a)
        self.assertEqual(ins["actor"], "")
        self.assertIn("光通信", ins["instruments"])
        self.assertIn("看多", ins["viewpoint"])
        self.assertNotIn("看空", ins["viewpoint"])

    def test_build_article_insight_line(self) -> None:
        a = Article(
            title="黄金走强",
            account="国投瑞银基金",
            keyword_found="黄金",
            url="https://example.com/gold",
            content="黄金看多，短期上行，建议超配黄金ETF。",
            source="test",
        )
        ins = build_article_insight(a)
        self.assertEqual(ins["actor"], "国投瑞银基金")
        self.assertIn("黄金", ins["instruments"])
        self.assertEqual(ins["direction"], "看多")
        self.assertIn("短期", ins["horizon"])
        self.assertIn("国投瑞银基金", ins["viewpoint"])
        self.assertIn("看多", ins["viewpoint"])

    def test_digest_contains_core_viewpoint(self) -> None:
        a = Article(
            title="原油承压",
            account="测试研究",
            keyword_found="原油",
            url="https://example.com/oil",
            content="原油看空，油价回落，中期承压。",
            source="test",
        )
        md = generate_digest_markdown([a], "2026-05-19")
        self.assertIn("**核心观点**", md)
        self.assertIn("**核心观点**", md)
        self.assertIn("本节观点速览", md)


if __name__ == "__main__":
    unittest.main()
