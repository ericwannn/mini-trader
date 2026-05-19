"""采集器抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from macro_collector.models import Article


class BaseCollector(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, max_items: Optional[int] = None) -> list[Article]:
        raise NotImplementedError
