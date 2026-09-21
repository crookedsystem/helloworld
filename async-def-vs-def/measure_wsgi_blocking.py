# /// script
# requires-python = ">=3.11"
# ///
"""동기 파이썬(WSGI)에서도 같은 현상이 생기는지 단일 스레드와 멀티 스레드로 나눠 잰다."""

import json
import sys
import threading
import time
import urllib.request
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

PORT = 8932
BASE = f"http://127.0.0.1:{PORT}"
BUSY_SECONDS = 10.0
OBSERVE_DELAY_SECONDS = 0.5


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args: object) -> None:
        pass


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def app(environ, start_response):
    if environ["PATH_INFO"] == "/busy":
        deadline = time.monotonic() + BUSY_SECONDS
        while time.monotonic() < deadline:
            pass
        body = json.dumps({"done": "busy"}).encode()
    else:
        body = json.dumps({"result": 1 + 1}).encode()
    start_response("200 OK", [("Content-Type", "application/json")])
    return [body]


def measure(server_cls: type[WSGIServer], label: str) -> None:
    server = make_server("127.0.0.1", PORT, app, server_class=server_cls, handler_class=QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def hit_busy() -> None:
        try:
            urllib.request.urlopen(f"{BASE}/busy", timeout=30).read()
        except Exception:
            pass

    blocker = threading.Thread(target=hit_busy, daemon=True)
    blocker.start()
    time.sleep(OBSERVE_DELAY_SECONDS)

    started_at = time.monotonic()
    try:
        with urllib.request.urlopen(f"{BASE}/add", timeout=20) as response:
            value = str(json.loads(response.read())["result"])
    except Exception as exc:
        value = f"실패({type(exc).__name__})"
    elapsed = time.monotonic() - started_at

    print(f"{label:34} {value:18} {elapsed:6.2f}s")
    blocker.join(timeout=25)
    server.shutdown()
    server.server_close()
    time.sleep(0.3)


def main() -> None:
    print(f"GIL 스위치 간격: {sys.getswitchinterval() * 1000:.1f} ms\n")
    print(f"{'WSGI 서버':34} {'/add 응답':18} {'지연'}")
    print("-" * 62)
    measure(WSGIServer, "단일 스레드 (순차 처리)")
    measure(ThreadingWSGIServer, "요청마다 스레드")


if __name__ == "__main__":
    main()
