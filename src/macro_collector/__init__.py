"""macro_collector — 每日宏观资产配置资讯采集与分析摘要生成。

功能:
  - A. 资讯采集: 公众号/华尔街见闻/金十数据/新浪财经
  - B. 宏观摘要: 结构化分析议题生成
  - C. 涨停复盘: A股涨停梯队+题材热度
  - D. 前端: FastAPI 可视化

使用:
  uv run macro-collector all       # 全流程
  uv run macro-collector collect   # 仅采集
  uv run macro-collector digest    # 仅摘要
  uv run macro-collector limitup   # 仅涨停复盘
  uv run macro-collector frontend  # 启动前端
"""

__all__: list[str] = []
