"""网络请求工具函数"""
import time
import random
import requests
from typing import Optional


def make_session() -> requests.Session:
    """创建一个带有标准请求头的 requests Session"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    return session


def gentle_delay(min_s: float = 1.0, max_s: float = 2.5):
    """随机延迟，避免触发反爬"""
    time.sleep(random.uniform(min_s, max_s))
