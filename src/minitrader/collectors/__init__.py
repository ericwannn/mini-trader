"""Collector 模块入口"""

from minitrader.collectors.jin10 import Jin10Collector
from minitrader.collectors.sina import SinaCollector
from minitrader.collectors.wallstreetcn import WallStreetCnCollector
from minitrader.collectors.wechat import WeChatCollector
from minitrader.config import wechat_enabled

ALL_COLLECTORS = []
if wechat_enabled():
    ALL_COLLECTORS.append(WeChatCollector())
ALL_COLLECTORS.extend([
    WallStreetCnCollector(),
    Jin10Collector(),
    SinaCollector(),
])

__all__ = [
    "ALL_COLLECTORS",
    "WeChatCollector",
    "WallStreetCnCollector",
    "Jin10Collector",
    "SinaCollector",
]
