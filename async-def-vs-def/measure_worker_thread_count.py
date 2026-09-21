# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "uvloop"]
# ///
"""워커 스레드가 async def 때문에 생기는지 def 때문에 생기는지 세어본다."""

import threading

from measurement_server import get_json, serve

PORT = 8934


def burst(path: str, count: int) -> None:
    threads = [threading.Thread(target=lambda: get_json(PORT, path), daemon=True) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)


def snapshot(label: str) -> None:
    counts = get_json(PORT, "/threads")
    print(f"{label:38} {counts['total']:>12} {counts['anyio_workers']:>12}")


def main() -> None:
    with serve("thread_count_app", PORT):
        print(f"{'시점':38} {'전체 스레드':>12} {'anyio 워커':>12}")
        print("-" * 66)
        snapshot("기동 직후")
        burst("/async-work", 50)
        snapshot("async def 엔드포인트 50회 호출 뒤")
        burst("/sync-work", 8)
        snapshot("def 엔드포인트 8개 동시 호출 뒤")


if __name__ == "__main__":
    main()
