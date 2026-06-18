# MiniTrader

[![仓库](https://img.shields.io/badge/GitHub-mini--trader-blue)](https://github.com/ericwannn/mini-trader)

个人交易辅助工具集。当前已实现的能力包括：

- **宏观资讯采集**：微信公众号（搜狗）、华尔街见闻、金十、新浪等
- **宏观摘要**：规则引擎或 LLM（OpenAI 兼容，含 **DeepSeek**）生成 Markdown 日报
- **涨停复盘**：A 股涨停梯队与题材热度（akshare）
- **Web 前端**：FastAPI 浏览摘要、文章与涨停数据

数据写入 `output/` 与根目录 `minitrader.db`（SQLite）。宏观采集只是其中一块，后续可继续扩展其它交易相关模块。

## 克隆与安装

```bash
git clone https://github.com/ericwannn/mini-trader.git
cd mini-trader
./scripts/install.sh
cp .env.example .env   # 按需填写 LLM / 微信代理等
```

本地目录名可与仓库名不同（例如 `daily_digest`），命令均在**项目根目录**执行。

## 快速使用

```bash
cd /path/to/mini-trader

# 安装包与依赖（推荐）
./scripts/install.sh
# 或: uv sync

# 采集多源数据 → output/raw/raw_<日期>.json + minitrader.db.articles
uv run minitrader collect

# 根据已有 raw 生成摘要 → output/digests/digest_<日期>.md + minitrader.db.digests + topics
uv run minitrader digest --date 2026-05-19

# 使用 LLM 生成摘要（需配置 API Key，见下文）
uv run minitrader digest --date 2026-05-19 --llm
# 或
uv run minitrader digest-llm --date 2026-05-19

# 一日全流程：采集 + 摘要 + 涨停复盘入库
uv run minitrader all

# A 股涨停复盘（akshare 东方财富，交易日 15:00 后才有完整数据）
uv run minitrader limitup

# 后台启动 Web 前端（推荐）
./scripts/minitrader-server.sh start
# 或: uv run minitrader serve start

# 前台调试（阻塞终端）
uv run minitrader frontend
```

> 在工程目录下执行 `uv run` 或 `scripts/*.sh`，避免外部 `VIRTUAL_ENV` 与本地 `.venv` 冲突。

## 安装与包入口

本项目为可安装的 Python 包 **`minitrader`**（源码在 `src/minitrader/`）：

| 入口 | 说明 |
|------|------|
| `minitrader` | 主 CLI：采集、摘要、涨停、服务管理 |
| `minitrader-server` | 等同 `minitrader serve`（仅 Web 后端管理） |
| `./scripts/minitrader.sh` | 包装 `uv run minitrader` |
| `./scripts/minitrader-server.sh` | 包装 `serve start/stop/restart/status` |
| `./scripts/install.sh` | `uv sync` + 初始化 `.env` / `output/` |

```bash
./scripts/install.sh
uv run minitrader --version
```

## Web 后端管理

| 命令 | 说明 |
|------|------|
| `./scripts/minitrader-server.sh start` | 后台启动，PID 写入 `output/minitrader-server.pid` |
| `./scripts/minitrader-server.sh stop` | 停止后台进程 |
| `./scripts/minitrader-server.sh restart` | 重启 |
| `./scripts/minitrader-server.sh status` | PID、健康检查、`output/minitrader-server.log` |

等价 CLI：

```bash
uv run minitrader serve start
uv run minitrader serve stop
uv run minitrader serve restart
uv run minitrader serve status
```

可选环境变量：`MINITRADER_SERVER_HOST`、`MINITRADER_SERVER_PORT`（默认 `0.0.0.0:8000`）。健康检查：`GET /health`。

## 手机远程访问（Tailscale）

无固定公网 IP 时推荐用 [Tailscale](https://tailscale.com) 组建私有网络，让手机用 4G/5G 也能访问家里 Mac 的 Web，且不暴露公网。当前 Web 前端无登录鉴权，**不建议**用 ngrok 等公网隧道方案直接暴露。

1. Mac 与手机分别安装 Tailscale 客户端，登录同一账号；
2. Mac 上启动服务：`./scripts/minitrader-server.sh start`（默认绑定 `0.0.0.0:8000`，Tailscale 虚拟网卡可直达）；
3. 查询 Mac 的 Tailscale IP：`tailscale ip -4`（或在 `minitrader serve status` 输出中查看 `Tailscale:` 行）；
4. 手机浏览器打开 `http://<mac的100.x.x.x>:8000/` 即可，建议存为书签；
5. 可在 Tailscale Admin → DNS 启用 **MagicDNS**，用机器名替代 IP。

注意：Mac 睡眠 / 关机或 Tailscale 离线时手机无法访问；切勿对该服务开启 Tailscale Funnel（公网分享）。

## 命令一览

| 子命令 | 作用 | 主要输出 |
|------|------|------|
| `collect` | 多源采集并去重 | `output/raw/raw_<date>.json`，`minitrader.db.articles` |
| `digest` | 由 raw JSON 生成 Markdown 日报（规则引擎，默认） | `output/digests/digest_<date>.md`，`minitrader.db.digests`，`minitrader.db.topics` |
| `digest --llm` / `digest-llm` | 调用 OpenAI 兼容 API 生成摘要 | 同上 |
| `limitup` | akshare 拉取当日 A 股涨停板 + 题材热度 | `minitrader.db.limitup_records / theme_heat` |
| `frontend` | 前台启动 Web（阻塞） | `http://localhost:8000` |
| `serve start` | 后台启动 Web | `output/minitrader-server.pid` + 日志 |
| `serve stop` / `restart` / `status` | 管理后台进程 | — |
| `all` | `collect` → `digest` → `limitup` 一站式 | 同时写文件与 DB |

`collect` 微信源支持 `--keywords / --per-keyword / --max-total` 调整搜索关键词与上限。

## 环境配置（`.env`）

在项目根目录复制 `.env.example` 为 `.env`（勿提交 Git）：

| 变量 | 说明 |
|------|------|
| `MINITRADER_WECHAT_ENABLED` | `0` 时跳过微信公众号采集 |
| `MINITRADER_WECHAT_PROXY` | 搜狗微信 HTTP(S) 代理，如 `http://127.0.0.1:7890` |
| `MINITRADER_WECHAT_COOKIE` | 浏览器访问 weixin.sogou.com 后的 Cookie，用于缓解验证码 |
| `MINITRADER_LLM_API_KEY` | LLM API Key（也可用 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY`） |
| `MINITRADER_LLM_BASE_URL` | OpenAI **兼容**端点；DeepSeek 填 `https://api.deepseek.com` |
| `MINITRADER_LLM_MODEL` | 模型名；DeepSeek 常用 `deepseek-chat`（未设置且 base 含 deepseek 时会自动选用） |
| `MINITRADER_SERVER_HOST` | Web 监听地址，默认 `0.0.0.0` |
| `MINITRADER_SERVER_PORT` | Web 端口，默认 `8000` |

程序启动时会自动加载根目录 `.env`（不覆盖已导出的系统环境变量）。旧版 `MACRO_*` 变量名仍可读，建议逐步改为 `MINITRADER_*`。

### DeepSeek 配置示例

```bash
MINITRADER_LLM_API_KEY=sk-你的DeepSeek密钥
MINITRADER_LLM_BASE_URL=https://api.deepseek.com
MINITRADER_LLM_MODEL=deepseek-chat
```

然后执行：`uv run minitrader digest --llm` 或 `uv run minitrader digest-llm`。

## 前端 Markdown 与结构化议题

摘要详情页（`/digest/<日期>`）会将 Markdown 服务端渲染为 HTML（`markdown` + `bleach` 白名单过滤）。
若已运行 `digest` 并写入 `topics` 表，页面顶部会展示结构化议题卡片（关键词、品种、方向、周期、逻辑、原文链接）。

## 定时任务

`scripts/collect.sh` 会在项目根目录执行 `uv run minitrader all`，并将输出写入
`output/collect_<日期>.log`，适合放在 cron 里：

```cron
30 17 * * 1-5 cd /path/to/mini-trader && ./scripts/collect.sh
```

## Cursor Agent Skills

主要工作流已固化为项目内 Skill（供 Cursor / Agent 按场景加载）：

| Skill | 路径 | 场景 |
|-------|------|------|
| 资讯采集 | `.cursor/skills/minitrader-collect/SKILL.md` | `collect`、采集器扩展 |
| 摘要生成 | `.cursor/skills/minitrader-digest/SKILL.md` | `digest` / `digest-llm`、议题与方向 |
| 涨停复盘 | `.cursor/skills/minitrader-limitup/SKILL.md` | `limitup`、akshare |
| Web 服务 | `.cursor/skills/minitrader-web/SKILL.md` | `serve` / `frontend` |
| 一日流程 | `.cursor/skills/minitrader-daily/SKILL.md` | `all`、cron、`collect.sh` |

## 项目结构

```
src/minitrader/
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
├── minitrader.sh   # CLI 包装
├── minitrader-server.sh      # Web 后端 start|stop|restart|status
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

minitrader.db                 # SQLite，前端读取来源（已加入 .gitignore）
```

`output/`、`artifacts/`、`.env` 不纳入版本库。`artifacts/` 可用于本地实验产物，无需上传。

旧版 `data/`、`collect_wechat.py` 等已废弃；若本地仍有 `data/raw/`，请迁移至 `output/raw/`。

## 验证清单

跑完一次 `uv run minitrader all` 后，最少应能确认：

```bash
ls output/raw/raw_$(date +%F).json
ls output/digests/digest_$(date +%F).md
sqlite3 minitrader.db "SELECT COUNT(*) FROM articles; SELECT COUNT(*) FROM digests;"
uv run minitrader frontend   # 浏览器访问 / 与 /digest/<日期>
```

- 交易日（15:00 之后）`limitup_records` 应有数据；非交易日 CLI 会打印 `已无可入库数据` 或
  akshare 返回的具体错误。
- 搜狗微信偶发触发验证码时会被跳过；可配置 `MINITRADER_WECHAT_COOKIE` / `MINITRADER_WECHAT_PROXY` 后重跑，或设置 `MINITRADER_WECHAT_ENABLED=0` 仅采集其他源。
- `digest` 默认使用本地规则引擎；`--llm` 需有效 API Key，否则会退出码 1 并提示配置方式。

## 开发与测试

```bash
uv sync
python -m unittest discover -s tests -v
```

## 版本

当前包版本见 `pyproject.toml` / `minitrader.__about__.__version__`（v0.4.0 起包名为 `minitrader`）。
