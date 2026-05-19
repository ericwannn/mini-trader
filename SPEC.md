# 项目完善需求规格

## 项目现状

已有库结构 (minitrader v0.2.0, uv 管理):

```
~/Investment/daily_digest/
├── pyproject.toml              # uv 项目, entry: minitrader
├── spec.md                     # 本文件
├── README.md
├── .gitignore
├── collect_wechat.py           # ❌ 旧平铺文件, 待删除
├── run_collect.sh              # ❌ 旧脚本, 待删除
├── data/                       # ❌ 旧数据目录, 待迁移
│   ├── raw/raw_2026-05-18.json
│   └── digests/digest_2026-05-18.md
├── output/
│   ├── raw/.gitkeep
│   └── digests/.gitkeep
├── scripts/
│   └── collect.sh              # cron 包装脚本
└── src/minitrader/
    ├── __init__.py
    ├── __about__.py             # __version__ = "0.2.0"
    ├── cli.py                   # collect / digest / all
    ├── models/
    │   ├── __init__.py          # Article dataclass (to_dict, from_dict)
    │   └── digest.py            # save_raw, load_raw, generate_intro_prompt
    ├── collectors/
    │   ├── __init__.py          # ❌ 空的, 需要导出
    │   └── wechat.py            # WeChatCollector ✓
    └── utils/
        ├── __init__.py          # make_session, gentle_delay
        └── network.py           # ❌ 空的重复文件
```

## 需要 cursor agent 完成的工作

按以下顺序执行：

### 1. 清理旧文件

- 删除 `collect_wechat.py`
- 删除 `run_collect.sh`
- 将 `data/raw/raw_2026-05-18.json` 移到 `output/raw/raw_2026-05-18.json`
- 将 `data/digests/digest_2026-05-18.md` 移到 `output/digests/digest_2026-05-18.md`
- 删除 `data/` 目录
- 删除 `utils/network.py`（内容已重复）

### 2. 完善 collectors/__init__.py

导出 WeChatCollector 和占位符给其他采集器。

```python
"""Collector 模块入口"""
from .wechat import WeChatCollector

ALL_COLLECTORS = [
    WeChatCollector(),
]

__all__ = ["ALL_COLLECTORS", "WeChatCollector"]
```

### 3. 实现华尔街见闻采集器 collectors/wallstreetcn.py

```python
"""华尔街见闻快讯采集器"""
class WallStreetCnCollector(BaseCollector):
    """华尔街见闻快讯采集"""
    
    source_name = "华尔街见闻"
    
    def __init__(self):
        self.session = make_session()
    
    def fetch(self, max_items: int = 30) -> list[Article]:
        """采集快讯"""
        url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"
        try:
            r = self.session.get(url, timeout=15)
            data = r.json()
            articles = []
            for item in data.get("data", {}).get("items", [])[:max_items]:
                articles.append(Article(
                    title=item.get("title", "") or item.get("content_text", "")[:60],
                    account="华尔街见闻",
                    keyword_found="global-channel",
                    url=f"https://wallstreetcn.com/live/global/{item.get('id', '')}",
                    content=item.get("content_text", ""),
                    publish_time=item.get("display_time", ""),
                    source="wallstreetcn",
                ))
            return articles
        except Exception as e:
            print(f"  ⚠️ 华尔街见闻采集失败: {e}")
            return []
```

### 4. 实现金十数据采集器 collectors/jin10.py

```python
"""金十数据快讯采集器"""
class Jin10Collector(BaseCollector):
    source_name = "金十数据"
    
    def __init__(self):
        self.session = make_session()
    
    def fetch(self, max_items: int = 30) -> list[Article]:
        """采集金十快讯"""
        headers = {"x-app-id": "bVBF4F9RT2OTfWfWltPbCQ==", "x-version": "1.0.0"}
        url = "https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=1&max_time="
        try:
            r = self.session.get(url, headers={**self.session.headers, **headers}, timeout=15)
            data = r.json()
            articles = []
            for item in data.get("data", [])[:max_items]:
                content = item.get("content", "")
                title = item.get("title", "") or content[:60]
                articles.append(Article(
                    title=title,
                    account="金十数据",
                    keyword_found="jin10_flash",
                    url=f"https://www.jin10.com/flash/{item.get('id', '')}",
                    content=content,
                    publish_time=item.get("time", ""),
                    source="jin10",
                ))
            return articles
        except Exception as e:
            print(f"  ⚠️ 金十数据采集失败: {e}")
            return []
```

### 5. 实现新浪财经采集器 collectors/sina.py

```python
"""新浪财经新闻采集器"""
class SinaCollector(BaseCollector):
    source_name = "新浪财经"
    
    def __init__(self):
        self.session = make_session()
    
    def fetch(self, max_items: int = 20) -> list[Article]:
        """采集新浪财经头条新闻"""
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1"
        try:
            r = self.session.get(url, timeout=15)
            data = r.json()
            articles = []
            for item in data.get("result", {}).get("data", [])[:max_items]:
                articles.append(Article(
                    title=item.get("title", ""),
                    account="新浪财经",
                    keyword_found="sina_roll",
                    url=item.get("link", ""),
                    content=item.get("intro", ""),
                    publish_time=item.get("ctime", ""),
                    source="sina",
                ))
            return articles
        except Exception as e:
            print(f"  ⚠️ 新浪财经采集失败: {e}")
            return []
```

### 6. 新增 base.py 采集器基类

创建 `collectors/base.py`:

```python
from abc import ABC, abstractmethod
from ..models import Article

class BaseCollector(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    def fetch(self) -> list[Article]:
        ...
```

### 7. 重写 cli.py — do_collect 支持多采集器

修改 `cli.py` 中的 `do_collect`，遍历 `ALL_COLLECTORS` 调用各自的 `fetch()`，合并所有文章后去重保存。

```python
from minitrader.collectors import ALL_COLLECTORS

def do_collect(args):
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== 宏观资产配置资讯采集: {today} ===\n")
    
    all_articles = []
    for collector in ALL_COLLECTORS:
        print(f"\n--- {collector.source_name} ---")
        try:
            articles = collector.fetch()
            all_articles.extend(articles)
            print(f"  采集 {len(articles)} 条")
        except Exception as e:
            print(f"  ⚠️ 失败: {e}")
    
    print(f"\n=== 采集完成: 共 {len(all_articles)} 条 ===")
    path = save_raw(all_articles, target_date=today)
    return path
```

### 8. 重写 do_digest — 直接生成完整的 Markdown 摘要文件

这是核心改动。`do_digest` 不再只是打印一个 prompt，而是：
1. 加载原始 JSON
2. 按议题分类（基于关键词匹配）
3. 生成完整的 Markdown 文件

**必须包含每篇文章的标题和原文链接**。

分类规则（关键词匹配）：

| 议题 | 匹配关键词 |
|------|-----------|
| 黄金/贵金属 | 黄金、金价、贵金属、避险 |
| 原油/能源 | 原油、石油、能源、OPEC、霍尔木兹 |
| A股/港股 | A股、港股、沪深、上证、创业板 |
| 美股 | 美股、标普、纳斯达克、道指 |
| 外汇/汇率 | 美元、人民币、汇率、外汇、美联储 |
| 债券/利率 | 债券、利率、国债、收益率 |
| 宏观政策 | 政策、GDP、经济数据、十五五、改革 |
| 大宗商品 | 大宗商品、铜、铁矿石、农产品 |

分类后每个议题格式如下：

```markdown
## N. 议题名称

### 文章: 文章标题
- **来源**: 公众号/来源名 | [原文链接](实际URL)
- **内容摘要**: (正文前200字)
- **涉及品种**: (提取提到的品种)
- **方向判断**: (看多/看空/中性)
- **预测周期**: (短期/中期/长期)
- **分析逻辑**: (逻辑链条)
```

完整文件结构:

```markdown
# 每日宏观资产配置摘要 — 2026-05-18

## 总体概述
(2-3句话概括今日核心议题)

---

## 1. 黄金/贵金属

### 文章: 黄金还能买吗
- **来源**: 国投瑞银基金 | [原文链接](https://mp.weixin.qq.com/...)
- **内容摘要**: ...
- **涉及品种**: 黄金、黄金ETF
- **方向判断**: 看涨
- **预测周期**: 中期(3-12月)
- **分析逻辑**: 1. ... 2. ... 3. ...

### 文章: 地缘冲突推动避险
- **来源**: 中信建投研究 | [原文链接](...)
- **涉及品种**: 黄金、原油
- **方向判断**: 看涨
- **预测周期**: 短期(1-3月)
- **分析逻辑**: ...

---

## 2. 原油/能源
...
```

### 9. 更新 scripts/collect.sh

cron 脚本应该执行 `uv run minitrader all` 来完成采集+生成摘要。

### 10. 更新 README.md

确保 README 反映最新结构和使用方式。

### 11. 更新 pyproject.toml

版本号升到 0.3.0。

## 验证标准

```bash
cd ~/Investment/daily_digest

# 安装/更新依赖
uv sync

# 测试采集
uv run minitrader collect

# 测试摘要生成（基于已有 raw 数据）
uv run minitrader digest --date 2026-05-18

# 测试完整流程
uv run minitrader all

# 检查生成的 digest 文件是否包含文章标题和原文链接
cat output/digests/digest_2026-05-18.md | head -50
```

## 执行方式

```bash
cd /Users/ericwan/Investment/daily_digest
cursor agent --print -p "请按 SPEC.md 的要求完善 minitrader 项目。先读取现有所有源码文件理解当前状态，然后按顺序执行所有步骤。注意使用 uv 而不是 pip。"
```
