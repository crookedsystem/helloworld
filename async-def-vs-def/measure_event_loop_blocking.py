# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "uvloop"]
# ///
"""무한루프 엔드포인트를 때린 직후 다른 API가 응답하는지 조합별로 잰다."""

import time

from measurement_server import call_and_ignore_result, measure_latency, serve

PORT = 8931
OBSERVE_DELAY_SECONDS = 0.5  # 블로킹 요청을 보낸 뒤 /add를 때리기까지 기다리는 시간

CASES = [
    ("uvloop", "/busy-async", "async def + 순수 busy loop"),
    ("uvloop", "/busy-sync", "def + 순수 busy loop"),
    ("uvloop", "/busy-async-yield", "async def + await 양보"),
    ("asyncio", "/busy-async", "async def + 순수 busy loop"),
    ("asyncio", "/busy-sync", "def + 순수 busy loop"),
]


def run_case(loop_impl: str, busy_path: str) -> tuple[str, float]:
    with serve("blocking_app", PORT, loop_impl):
        blocker = call_and_ignore_result(PORT, busy_path)
        time.sleep(OBSERVE_DELAY_SECONDS)
        result = measure_latency(PORT, "/add")
        blocker.join(timeout=25)
        return result


def main() -> None:
    print(f"{'루프':10} {'블로킹 엔드포인트':28} {'/add 응답':18} {'지연'}")
    print("-" * 74)
    for loop_impl, busy_path, label in CASES:
        value, elapsed = run_case(loop_impl, busy_path)
        print(f"{loop_impl:10} {label:28} {value:18} {elapsed:6.2f}s")


if __name__ == "__main__":
    main()
