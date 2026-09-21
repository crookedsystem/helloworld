# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "uvloop"]
# ///
"""CPU를 태우는 def 엔드포인트가 40개 돌 때 다른 엔드포인트들이 어떻게 되는지 잰다."""

import threading
import time

from measurement_server import call_and_ignore_result, measure_latency, serve

PORT = 8933
BLOCKER_COUNT = 40  # anyio 기본 리미터 토큰 수와 같은 수
SETTLE_SECONDS = 2.0  # 모든 blocker가 워커 스레드를 실제로 붙들 때까지 기다린다


def run(blockers: int) -> dict[str, tuple[str, float]]:
    with serve("blocking_app", PORT):
        busy = [call_and_ignore_result(PORT, "/busy-sync") for _ in range(blockers)]
        if blockers:
            time.sleep(SETTLE_SECONDS)

        # 두 엔드포인트를 동시에 재지 않으면, 먼저 잰 쪽이 끝나는 동안 blocker도 끝나버려
        # 나중에 잰 값이 한가한 서버를 측정하게 된다.
        results: dict[str, tuple[str, float]] = {}

        def probe(key: str, path: str) -> None:
            results[key] = measure_latency(PORT, path)

        probes = [
            threading.Thread(target=probe, args=("async", "/add"), daemon=True),
            threading.Thread(target=probe, args=("sync", "/add-sync"), daemon=True),
        ]
        for thread in probes:
            thread.start()
        for thread in probes:
            thread.join(timeout=70)
        for thread in busy:
            thread.join(timeout=60)
        return results


def main() -> None:
    print(f"{'상황':30} {'async def /add':>18} {'def /add-sync':>18}")
    print("-" * 70)
    for blockers, label in ((0, "블로커 없음 (기준선)"), (BLOCKER_COUNT, f"CPU busy def {BLOCKER_COUNT}개 실행 중")):
        results = run(blockers)
        async_value, async_seconds = results.get("async", ("없음", 0.0))
        sync_value, sync_seconds = results.get("sync", ("없음", 0.0))
        print(f"{label:30} {async_value + ' / ' + format(async_seconds, '.2f') + 's':>18}"
              f" {sync_value + ' / ' + format(sync_seconds, '.2f') + 's':>18}")


if __name__ == "__main__":
    main()
