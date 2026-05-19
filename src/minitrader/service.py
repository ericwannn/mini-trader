"""FastAPI 后端进程管理 — start / stop / restart / status"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from minitrader.config import PROJECT_DIR, server_host, server_port

OUTPUT_DIR = PROJECT_DIR / "output"
PID_FILE = OUTPUT_DIR / "minitrader-server.pid"
LOG_FILE = OUTPUT_DIR / "minitrader-server.log"


def _public_url(host: str, port: int) -> str:
    display = "localhost" if host in ("0.0.0.0", "::", "") else host
    return f"http://{display}:{port}"


def read_pid() -> Optional[int]:
    if not PID_FILE.is_file():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_running() -> bool:
    pid = read_pid()
    if pid is None:
        return False
    if _pid_alive(pid):
        return True
    _remove_pid_file()
    return False


def _write_pid(pid: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _remove_pid_file() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _health_check(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str | None]:
    """返回 (是否 200, health JSON 中的 service 字段)。"""
    url = f"{_public_url(host, port)}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False, None
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("status") == "ok", body.get("service")
    except (urllib.error.URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError):
        return False, None


def _health_ok(host: str, port: int, timeout: float = 2.0) -> bool:
    ok, service = _health_check(host, port, timeout)
    return ok and service == "minitrader"


def start_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    foreground: bool = False,
) -> int:
    """启动 uvicorn；默认后台守护，--foreground 时前台阻塞。"""
    from minitrader.db import init_db

    host = host or server_host()
    port = port or server_port()
    init_db()

    if is_running():
        pid = read_pid()
        print(f"服务已在运行 (PID {pid}) — {_public_url(host, port)}")
        return 0

    port_ok, port_service = _health_check(host, port, timeout=0.8)
    if port_ok and port_service != "minitrader":
        print(
            f"端口 {port} 已被旧版服务占用 (health service={port_service!r})，"
            "请先停止旧进程再启动 MiniTrader："
        )
        print(f"  lsof -i :{port}")
        print(f"  kill <PID>   # 或: ./scripts/minitrader-server.sh restart")
        return 1

    if foreground:
        import uvicorn

        from minitrader.frontend.app import app

        print("=== 启动前端（前台）===")
        print(f"访问地址: {_public_url(host, port)}")
        uvicorn.run(app, host=host, port=port, log_level="info")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_handle = open(LOG_FILE, "a", encoding="utf-8")
    log_handle.write(f"\n--- start {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    log_handle.flush()

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "minitrader.frontend.app:app",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "info",
        ],
        cwd=str(PROJECT_DIR),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    _write_pid(proc.pid)

    for _ in range(20):
        if proc.poll() is not None:
            print(f"启动失败，进程已退出 (code={proc.returncode})，请查看日志: {LOG_FILE}")
            _remove_pid_file()
            return 1
        if _health_ok(host, port, timeout=0.5):
            break
        time.sleep(0.15)
    else:
        if proc.poll() is None:
            print(f"已启动 PID {proc.pid}（健康检查未确认，可能仍在加载）")
        else:
            print(f"启动失败，请查看日志: {LOG_FILE}")
            _remove_pid_file()
            return 1

    print(f"已启动 PID {proc.pid}")
    print(f"访问地址: {_public_url(host, port)}")
    print(f"日志: {LOG_FILE}")
    return 0


def stop_server() -> int:
    pid = read_pid()
    if pid is None:
        print("服务未运行（无 PID 文件）")
        return 0
    if not _pid_alive(pid):
        print(f"服务未运行（陈旧 PID {pid}，已清理）")
        _remove_pid_file()
        return 0

    print(f"正在停止 PID {pid} ...")
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        print(f"停止失败: {e}")
        return 1

    for _ in range(50):
        if not _pid_alive(pid):
            break
        time.sleep(0.1)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    _remove_pid_file()
    print("服务已停止")
    return 0


def restart_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> int:
    stop_server()
    time.sleep(0.3)
    return start_server(host=host, port=port, foreground=False)


def status_server() -> int:
    host = server_host()
    port = server_port()
    pid = read_pid()
    url = _public_url(host, port)

    if pid is None or not _pid_alive(pid):
        if pid is not None:
            _remove_pid_file()
        print("状态: 未运行")
        print(f"启动: uv run minitrader serve start  或  ./scripts/minitrader-server.sh start")
        return 1

    port_ok, port_service = _health_check(host, port)
    healthy = port_ok and port_service == "minitrader"
    print(f"状态: 运行中 (PID {pid})")
    print(f"地址: {url}")
    if healthy:
        print("健康: OK")
    elif port_ok and port_service != "minitrader":
        print(f"健康: 端口被其它服务占用 (service={port_service!r})，请 kill 旧进程后 restart")
    else:
        print("健康: 无响应（可能仍在启动或端口被占用）")
    print(f"日志: {LOG_FILE}")
    return 0 if healthy else 2


def _build_serve_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="minitrader serve", description="管理 FastAPI 后端")
    sub = parser.add_subparsers(dest="action", required=True)

    p_start = sub.add_parser("start", help="后台启动服务")
    p_start.add_argument("--host", default=None, help="监听地址，默认 MINITRADER_SERVER_HOST 或 0.0.0.0")
    p_start.add_argument("--port", type=int, default=None, help="端口，默认 MINITRADER_SERVER_PORT 或 8000")
    p_start.add_argument(
        "-f",
        "--foreground",
        action="store_true",
        help="前台运行（等同 minitrader frontend）",
    )

    sub.add_parser("stop", help="停止后台服务")

    p_restart = sub.add_parser("restart", help="重启后台服务")
    p_restart.add_argument("--host", default=None)
    p_restart.add_argument("--port", type=int, default=None)

    sub.add_parser("status", help="查看运行状态")
    return parser


def serve_main(argv: list[str] | None = None) -> None:
    parser = _build_serve_parser()
    args = parser.parse_args(argv)
    code = 0
    if args.action == "start":
        code = start_server(host=args.host, port=args.port, foreground=args.foreground)
    elif args.action == "stop":
        code = stop_server()
    elif args.action == "restart":
        code = restart_server(host=args.host, port=args.port)
    elif args.action == "status":
        code = status_server()
    sys.exit(code)


def main() -> None:
    """独立入口 minitrader-server（可选）。"""
    serve_main()
