# Macro Collector — 每日宏观资产配置资讯采集

从**微信公众号**（搜狗微信搜索）、**华尔街见闻**、**金十数据**、**新浪财经**等来源采集快讯与
文章，合并去重后保存原始 JSON，按议题归类生成本地 **Markdown** 摘要，并将文章 / 摘要 / A 股
**涨停复盘** 数据同步写入根目录的 `macro.db`（SQLite），可通过内置 FastAPI 前端查看。

## 快速使用

```bash
cd ~/Investment/daily_digest

# 安装包与依赖（推荐）
./scripts/install.sh
# 或: uv sync

# 采集多源数据 → output/raw/raw_<日期>.json + macro.db.articles
uv run macro-collector collect

# 根据已有 raw 生成摘要 → output/digests/digest_<日期>.md + macro.db.digests + topics
uv run macro-collector digest --date 2026-05-19

# 使用 LLM 生成摘要（需配置 API Key，见下文）
uv run macro-collector digest --date 2026-05-19 --llm
# 或
uv run macro-collector digest-llm --date 2026-05-19

# 一日全流程：采集 + 摘要 + 涨停复盘入库
uv run macro-collector all

# A 股涨停复盘（akshare 东方财富，交易日 15:00 后才有完整数据）
uv run macro-collector limitup

# 后台启动 Web 前端（推荐）
./scripts/macro-server.sh start
# 或: uv run macro-collector serve start

# 前台调试（阻塞终端）
uv run macro-collector frontend
```

> 在工程目录下执行 `uv run` 或 `scripts/*.sh`，避免外部 `VIRTUAL_ENV` 与本地 `.venv` 冲突。

## 安装与包入口

本项目为可安装的 Python 包 **`macro-collector`**（源码在 `src/macro_collector/`）：

| 入口 | 说明 |
|------|------|
| `macro-collector` | 主 CLI：采集、摘要、涨停、服务管理 |
| `macro-server` | 等同 `macro-collector serve`（仅 Web 后端管理） |
| `./scripts/macro-collector.sh` | 包装 `uv run macro-collector` |
| `./scripts/macro-server.sh` | 包装 `serve start/stop/restart/status` |
| `./scripts/install.sh` | `uv sync` + 初始化 `.env` / `output/` |

```bash
./scripts/install.sh
uv run macro-collector --version
```

## Web 后端管理

| 命令 | 说明 |
|------|------|
| `./scripts/macro-server.sh start` | 后台启动，PID 写入 `output/macro-server.pid` |
| `./scripts/macro-server.sh stop` | 停止后台进程 |
| `./scripts/macro-server.sh restart` | 重启 |
| `./scripts/macro-server.sh status` | PID、健康检查、`output/macro-server.log` |

等价 CLI：

```bash
uv run macro-collector serve start
uv run macro-collector serve stop
uv run macro-collector serve restart
uv run macro-collector serve status
```

可选环境变量：`MACRO_SERVER_HOST`、`MACRO_SERVER_PORT`（默认 `0.0.0.0:8000`）。健康检查：`GET /health`。

## 命令一览

| 子命令 | 作用 | 主要输出 |
|------|------|------|
| `collect` | 多源采集并去重 | `output/raw/raw_<date>.json`，`macro.db.articles` |
| `digest` | 由 raw JSON 生成 Markdown 日报（规则引擎，默认） | `output/digests/digest_<date>.md`，`macro.db.digests`，`macro.db.topics` |
| `digest --llm` / `digest-llm` | 调用 OpenAI 兼容 API 生成摘要 | 同上 |
| `limitup` | akshare 拉取当日 A 股涨停板 + 题材热度 | `macro.db.limitup_records / theme_heat` |
| `frontend` | 前台启动 Web（阻塞） | `http://localhost:8000` |
| `serve start` | 后台启动 Web | `output/macro-server.pid` + 日志 |
| `serve stop` / `restart` / `status` | 管理后台进程 | — |
| `all` | `collect` → `digest` → `limitup` 一站式 | 同时写文件与 DB |

`collect` 微信源支持 `--keywords / --per-keyword / --max-total` 调整搜索关键词与上限。

## 环境配置（`.env`）

在项目根目录复制 `.env.example` 为 `.env`（勿提交 Git）：

| 变量 | 说明 |
|------|------|
| `MACRO_WECHAT_ENABLED` | `0` 时跳过微信公众号采集 |
| `MACRO_WECHAT_PROXY` | 搜狗微信 HTTP(S) 代理，如 `http://127.0.0.1:7890` |
| `MACRO_WECHAT_COOKIE` | 浏览器访问 weixin.sogou.com 后的 Cookie，用于缓解验证码 |
| `MACRO_LLM_API_KEY` | LLM API Key（也可用 `OPENAI_API_KEY`） |
| `MACRO_LLM_BASE_URL` | OpenAI 兼容端点，默认 `https://api.openai.com/v1` |
| `MACRO_LLM_MODEL` | 模型名，默认 `gpt-4o-mini` |
| `MACRO_SERVER_HOST` | Web 监听地址，默认 `0.0.0.0` |
| `MACRO_SERVER_PORT` | Web 端口，默认 `8000` |

程序启动时会自动加载根目录 `.env`（不覆盖已导出的系统环境变量）。

## 前端 Markdown 与结构化议题

摘要详情页（`/digest/<日期>`）会将 Markdown 服务端渲染为 HTML（`markdown` + `bleach` 白名单过滤）。
若已运行 `digest` 并写入 `topics` 表，页面顶部会展示结构化议题卡片（关键词、品种、方向、周期、逻辑、原文链接）。

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
├── cli.py               # collect / digest / limitup / frontend / serve / all
├── service.py           # Web 后端 start/stop/restart/status
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

scripts/
├── install.sh           # uv sync + 初始化
├── macro-collector.sh   # CLI 包装
├── macro-server.sh      # Web 后端 start|stop|restart|status
├── collect.sh           # cron 一日采集
└── send_digest.sh       # 摘要精简输出
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
- 搜狗微信偶发触发验证码时会被跳过；可配置 `MACRO_WECHAT_COOKIE` / `MACRO_WECHAT_PROXY` 后重跑，或设置 `MACRO_WECHAT_ENABLED=0` 仅采集其他源。
- `digest` 默认使用本地规则引擎；`--llm` 需有效 API Key，否则会退出码 1 并提示配置方式。

## 版本

当前包版本见 `pyproject.toml` / `macro_collector.__about__.__version__`。
