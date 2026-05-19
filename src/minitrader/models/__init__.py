"""文章数据模型和 Article 数据类"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


SOURCE_LABELS = {
    "sogou_wechat": "微信公众号",
    "sogou_wechat_fallback": "微信公众号",
    "wallstreetcn": "华尔街见闻",
    "jin10": "金十数据",
    "sina": "新浪财经",
}


def friendly_source(source: str) -> str:
    """将内部源标识映射为中文显示名，未知则原样返回。"""
    return SOURCE_LABELS.get(source, source or "")


@dataclass
class Article:
    """一篇采集到的文章"""
    title: str                           # 文章标题
    account: str                         # 公众号/来源名称
    keyword_found: str                   # 通过哪个关键词找到的
    url: str                             # 原文链接
    content: str = ""                    # 正文内容（截断）
    sogou_abstract: str = ""             # 搜狗搜索摘要
    publish_time: str = ""               # 发布时间
    source: str = "sogou_wechat"         # 数据源标识

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "account": self.account,
            "keyword_found": self.keyword_found,
            "url": self.url,
            "content": self.content,
            "sogou_abstract": self.sogou_abstract,
            "publish_time": self.publish_time,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Article:
        data = dict(d)
        fields = {k: data.get(k, "") for k in cls.__dataclass_fields__}
        if not fields.get("url") and data.get("wechat_url"):
            fields["url"] = str(data["wechat_url"])
        if not fields.get("account") and data.get("sogou_account"):
            acc = str(data["sogou_account"])
            fields["account"] = acc.rstrip(")").strip()
        return cls(**fields)
