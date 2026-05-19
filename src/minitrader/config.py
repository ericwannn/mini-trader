"""环境变量与可选 .env 配置加载（项目根目录 `.env`，不提交版本库）。"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """从项目根 `.env` 读取 KEY=VALUE，不覆盖已存在的环境变量。"""
    env_path = PROJECT_DIR / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env(*keys: str, default: str = "") -> str:
    """按顺序读取环境变量，兼容旧版 MACRO_* 命名。"""
    for key in keys:
        val = os.environ.get(key)
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return default


_load_dotenv()


def wechat_enabled() -> bool:
    """MINITRADER_WECHAT_ENABLED=0 时跳过微信公众号采集。"""
    val = _env("MINITRADER_WECHAT_ENABLED", "MACRO_WECHAT_ENABLED", default="1").lower()
    return val not in ("0", "false", "no", "off")


def wechat_proxy() -> str | None:
    proxy = _env("MINITRADER_WECHAT_PROXY", "MACRO_WECHAT_PROXY")
    return proxy or None


def wechat_cookie() -> str | None:
    cookie = _env("MINITRADER_WECHAT_COOKIE", "MACRO_WECHAT_COOKIE")
    return cookie or None


def llm_api_key() -> str | None:
    key = _env(
        "MINITRADER_LLM_API_KEY",
        "MACRO_LLM_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
    )
    return key or None


def llm_base_url() -> str:
    return _env(
        "MINITRADER_LLM_BASE_URL",
        "MACRO_LLM_BASE_URL",
        "DEEPSEEK_BASE_URL",
        "OPENAI_BASE_URL",
        default="https://api.openai.com/v1",
    ).rstrip("/")


def llm_model() -> str:
    explicit = _env("MINITRADER_LLM_MODEL", "MACRO_LLM_MODEL")
    if explicit:
        return explicit
    base = llm_base_url().lower()
    if "deepseek" in base:
        return "deepseek-chat"
    return "gpt-4o-mini"


def server_host() -> str:
    return _env("MINITRADER_SERVER_HOST", "MACRO_SERVER_HOST", default="0.0.0.0") or "0.0.0.0"


def server_port() -> int:
    raw = _env("MINITRADER_SERVER_PORT", "MACRO_SERVER_PORT", default="8000")
    try:
        return int(raw)
    except ValueError:
        return 8000
