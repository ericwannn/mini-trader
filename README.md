# Macro Collector — 每日宏观资产配置资讯采集

从**微信公众号**（搜狗微信搜索）、**华尔街见闻**、**金十数据**、**新浪财经**等来源采集快讯与
文章，合并去重后保存原始 JSON，按议题归类生成本地 **Markdown** 摘要，并将文章 / 摘要 / A 股
**涨停复盘** 数据同步写入根目录的 `macro.db`（SQLite），可通过内置 FastAPI 前端查看。

## 快速使用

```bash
cd ~/Investment/daily_digest

# 安装依赖（使用 uv，含 akshare）
uv sync

# 采集多源数据 → output/raw/raw_<日期>.json + macro.db.articles
uv run macro-collector collect

# 根据已有 raw 生成摘要 → output/digests/digest_<日期>.md + macro.db.digests
uv run macro-collector digest --date 2026-05-19

# 一日全流程：采集 + 摘要 + 涨停复盘入库
uv run macro-collector all

# A 股涨停复盘（akshare 东方财富，交易日 15:00 后才有完整数据）
uv run macro-collector limitup

# 启动可视化前端：http://localhost:8000
uv run macro-collector frontend
```

> 在工程目录下执行 `uv run`，避免外部 `VIRTUAL_ENV` 与本地 `.venv` 冲突。

## 命令一览

| 子命令 | 作用 | 主要输出 |
|------|------|------|
| `collect` | 多源采集并去重 | `output/raw/raw_<date>.json`，`macro.db.articles` |
| `digest` | 由 raw JSON 生成 Markdown 日报（按议题分组） | `output/digests/digest_<date>.md`，`macro.db.digests` |
| `limitup` | akshare 拉取当日 A 股涨停板 + 题材热度 | `macro.db.limitup_records / theme_heat` |
| `frontend` | 启动 FastAPI 前端 | `http://localhost:8000`（摘要 / 涨停 / 搜索） |
| `all` | `collect` → `digest` → `limitup` 一站式 | 同时写文件与 DB |

`collect` 微信源支持 `--keywords / --per-keyword / --max-total` 调整搜索关键词与上限。

## 定时任务

`scripts/collect.sh` 会在项目根目录执行 `uv run macro-collector all`，并将输出写入
`output/collect_<日期>.log`，适合放在 cron 里：

```cron
30 17 * * 1-5 cd ~/Investment/daily_digest && ./scripts/collect.sh
```

## 项目结构

```
src/macro_collector/
├── __about__.py         # 版本号
├── cli.py               # collect / digest / limitup / frontend / all
├── collectors/
│   ├── base.py          # BaseCollector
│   ├── wechat.py        # 搜狗微信搜索
│   ├── wallstreetcn.py  # 华尔街见闻快讯
│   ├── jin10.py         # 金十 flash_newest.js（JSON 主路径 + HTML 回退）
│   └── sina.py          # 新浪财经滚动
├── models/
│   ├── __init__.py      # Article + SOURCE_LABELS
│   └── digest.py        # save_raw / load_raw / 摘要 Markdown 生成
├── db/
│   ├── schema.sql       # SQLite 表结构
│   ├── models.py        # CRUD
│   └── sync.py          # persist_articles / persist_digest
├── limitup/
│   └── collector.py     # akshare 涨停 + 题材热度
├── frontend/
│   ├── app.py           # FastAPI + Jinja2
│   └── templates/
└── utils/
    └── __init__.py      # make_session, gentle_delay
```

## 输出目录

```
output/
├── raw/                 # 原始 JSON
│   └── raw_YYYY-MM-DD.json
├── digests/             # Markdown 摘要
│   └── digest_YYYY-MM-DD.md
└── collect_YYYY-MM-DD.log   # collect.sh 日志（若使用脚本）

macro.db                 # SQLite，前端读取来源（已加入 .gitignore）
```

旧版仓库根目录下的 `data/`、`collect_wechat.py`、`run_collect.sh` 已按 SPEC 废弃；若本地仍有
`data/raw/`，请迁移至 `output/raw/` 后再运行 `digest`。

## 验证清单

跑完一次 `uv run macro-collector all` 后，最少应能确认：

```bash
ls output/raw/raw_$(date +%F).json
ls output/digests/digest_$(date +%F).md
sqlite3 macro.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM digests;"
uv run macro-collector frontend   # 浏览器访问 / 与 /digest/<日期>
```

- 交易日（15:00 之后）`limitup_records` 应有数据；非交易日 CLI 会打印 `已无可入库数据` 或
  akshare 返回的具体错误。
- 搜狗微信偶发触发验证码时会被跳过，可重跑或在 `--keywords` 中减少关键词。

## 版本

当前包版本见 `pyproject.toml` / `macro_collector.__about__.__version__`。
