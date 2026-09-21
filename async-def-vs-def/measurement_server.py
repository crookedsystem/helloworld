"""측정 스크립트들이 공통으로 쓰는 uvicorn 기동과 HTTP 조회."""

import json
import pathlib
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
READY_TIMEOUT_SECONDS = 20.0


def base_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def get_json(port: int, path: str, timeout: float = 30.0) -> dict:
    with urllib.request.urlopen(f"{base_url(port)}{path}", timeout=timeout) as response:
        return json.loads(response.read())


def call_and_ignore_result(port: int, path: str, timeout: float = 60.0) -> threading.Thread:
    """응답을 기다리지 않고 요청만 걸어둔다. 블로킹 엔드포인트를 띄울 때 쓴다."""

    def body() -> None:
        try:
            urllib.request.urlopen(f"{base_url(port)}{path}", timeout=timeout).read()
        except Exception:
            pass

    thread = threading.Thread(target=body, daemon=True)
    thread.start()
    return thread


def measure_latency(port: int, path: str, timeout: float = 60.0) -> tuple[str, float]:
    """응답 값과 걸린 시간을 함께 돌려준다. 실패하면 값 자리에 실패 사유가 들어간다."""
    started_at = time.monotonic()
    try:
        payload = get_json(port, path, timeout=timeout)
        value = str(payload.get("result", payload))
    except Exception as exc:
        value = f"실패({type(exc).__name__})"
    return value, time.monotonic() - started_at


@contextmanager
def serve(app_module: str, port: int, loop_impl: str = "uvloop") -> Iterator[None]:
    """uvicorn을 별도 프로세스로 띄우고, 블록을 벗어나면 확실히 내린다."""
    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", f"{app_module}:app",
            "--port", str(port), "--loop", loop_impl, "--log-level", "warning",
        ],
        cwd=SCRIPT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(f"{base_url(port)}/openapi.json", timeout=0.5).read()
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError(f"{app_module} 서버가 {READY_TIMEOUT_SECONDS}초 안에 뜨지 않았다")
        yield
    finally:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        time.sleep(0.5)
