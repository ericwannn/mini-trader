"""FastAPI 后端进程管理 — start / stop / restart / status"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from macro_collector.config import PROJECT_DIR

OUTPUT_DIR = PROJECT_DIR / "output"
PID_FILE = OUTPUT_DIR / "macro-server.pid"
LOG_FILE = OUTPUT_DIR / "macro-server.log"


def server_host() -> str:
    return os.environ.get("MACRO_SERVER_HOST", "0.0.0.0").strip() or "0.0.0.0"


def server_port() -> int:
    raw = os.environ.get("MACRO_SERVER_PORT", "8000").strip()
    try:
        return int(raw)
    except ValueError:
        return 8000


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


def _health_ok(host: str, port: int, timeout: float = 2.0) -> bool:
    url = f"{_public_url(host, port)}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def start_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    foreground: bool = False,
) -> int:
    """启动 uvicorn；默认后台守护，--foreground 时前台阻塞。"""
    from macro_collector.db import init_db

    host = host or server_host()
    port = port or server_port()
    init_db()

    if is_running():
        pid = read_pid()
        print(f"服务已在运行 (PID {pid}) — {_public_url(host, port)}")
        return 0

    if foreground:
        import uvicorn

        from macro_collector.frontend.app import app

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
            "macro_collector.frontend.app:app",
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
        print(f"启动: uv run macro-collector serve start  或  ./scripts/macro-server.sh start")
        return 1

    healthy = _health_ok(host, port)
    print(f"状态: 运行中 (PID {pid})")
    print(f"地址: {url}")
    print(f"健康: {'OK' if healthy else '无响应（可能仍在启动或端口被占用）'}")
    print(f"日志: {LOG_FILE}")
    return 0 if healthy else 2


def _build_serve_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macro-collector serve", description="管理 FastAPI 后端")
    sub = parser.add_subparsers(dest="action", required=True)

    p_start = sub.add_parser("start", help="后台启动服务")
    p_start.add_argument("--host", default=None, help="监听地址，默认 MACRO_SERVER_HOST 或 0.0.0.0")
    p_start.add_argument("--port", type=int, default=None, help="端口，默认 MACRO_SERVER_PORT 或 8000")
    p_start.add_argument(
        "-f",
        "--foreground",
        action="store_true",
        help="前台运行（等同 macro-collector frontend）",
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
    """独立入口 macro-server（可选）。"""
    serve_main()
