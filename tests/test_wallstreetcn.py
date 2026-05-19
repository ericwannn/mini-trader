import unittest

from minitrader.collectors.wallstreetcn import wallstreetcn_live_url


class TestWallStreetCnUrl(unittest.TestCase):
    def test_prefers_api_uri(self):
        item = {
            "id": 3105766,
            "uri": "https://wallstreetcn.com/livenews/3105766",
        }
        self.assertEqual(wallstreetcn_live_url(item), item["uri"])

    def test_fallback_livenews_path(self):
        item = {"id": 3105766}
        self.assertEqual(
            wallstreetcn_live_url(item),
            "https://wallstreetcn.com/livenews/3105766",
        )


if __name__ == "__main__":
    unittest.main()
