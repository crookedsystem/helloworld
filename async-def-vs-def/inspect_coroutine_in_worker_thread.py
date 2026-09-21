# /// script
# requires-python = ">=3.11"
# dependencies = ["anyio"]
# ///
"""코루틴 함수를 워커 스레드에 넘기면 무슨 일이 나는지 그대로 재현한다."""

import asyncio
import threading

import anyio.to_thread


async def compute() -> int:
    await asyncio.sleep(0)
    return 42


def sync_compute() -> int:
    return 42


def look_for_running_loop() -> str:
    try:
        asyncio.get_running_loop()
        return "있음"
    except RuntimeError as exc:
        return f"없음 ({exc})"


def call_async_function_from_plain_thread() -> object:
    """anyio 워커가 실제로 하는 일과 같다. context.run(func)은 그냥 호출이다."""
    captured: dict[str, object] = {}

    def worker() -> None:
        captured["returned"] = compute()

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    return captured["returned"]


async def main() -> None:
    returned = call_async_function_from_plain_thread()
    print(f"[1] 스레드에서 async 함수를 호출한 결과 : {type(returned).__name__} -> {returned!r}")
    print("    42가 아니라 코루틴 객체다. 실행된 적이 없다.")
    returned.close()

    sync_result = await anyio.to_thread.run_sync(sync_compute)
    print(f"\n[2] to_thread.run_sync(동기 함수)  : {type(sync_result).__name__} -> {sync_result!r}")

    coroutine_result = await anyio.to_thread.run_sync(compute)
    print(f"[3] to_thread.run_sync(async 함수) : {type(coroutine_result).__name__} -> {coroutine_result!r}")
    print("    스레드는 코루틴을 돌릴 수 없다. 껍데기만 돌려받는다.")
    coroutine_result.close()

    print(f"\n[4] 워커 스레드에서 본 이벤트 루프 : {await anyio.to_thread.run_sync(look_for_running_loop)}")
    print(f"    메인(루프) 스레드에서 본 이벤트 루프 : {look_for_running_loop()}")


if __name__ == "__main__":
    asyncio.run(main())
