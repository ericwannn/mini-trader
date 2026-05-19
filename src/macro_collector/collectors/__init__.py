"""Collector 模块入口"""

from macro_collector.collectors.jin10 import Jin10Collector
from macro_collector.collectors.sina import SinaCollector
from macro_collector.collectors.wallstreetcn import WallStreetCnCollector
from macro_collector.collectors.wechat import WeChatCollector
from macro_collector.config import wechat_enabled

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
