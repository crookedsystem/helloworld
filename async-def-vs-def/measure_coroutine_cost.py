# /// script
# requires-python = ">=3.11"
# ///
"""코루틴과 스레드를 같은 개수 만들 때의 비용을 나란히 잰다."""

import asyncio
import sys
import threading
import time
import tracemalloc

COUNT = 10_000


async def noop() -> None:
    await asyncio.sleep(0)


async def coroutine_cost() -> tuple[int, float, int]:
    one = noop()
    size = sys.getsizeof(one)
    one.close()

    tracemalloc.start()
    started_at = time.perf_counter()
    await asyncio.gather(*(noop() for _ in range(COUNT)))
    elapsed = time.perf_counter() - started_at
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return size, elapsed, peak


def thread_cost(count: int) -> float:
    done = threading.Event()
    lock = threading.Lock()
    finished = 0

    def body() -> None:
        nonlocal finished
        with lock:
            finished += 1
            if finished == count:
                done.set()

    started_at = time.perf_counter()
    threads = [threading.Thread(target=body) for _ in range(count)]
    for thread in threads:
        thread.start()
    done.wait()
    for thread in threads:
        thread.join()
    return time.perf_counter() - started_at


def main() -> None:
    size, coroutine_elapsed, coroutine_peak = asyncio.run(coroutine_cost())
    print(f"코루틴 객체 1개          : {size} bytes")
    print(f"코루틴 {COUNT}개 동시 실행 : {coroutine_elapsed * 1000:.1f} ms, 피크 {coroutine_peak / 1024 / 1024:.2f} MiB")
    for count in (1_000, COUNT):
        print(f"스레드 {count}개 생성+실행: {thread_cost(count) * 1000:.1f} ms")
    print(f"기본 스레드 스택 예약     : {threading.stack_size()} (0 = OS 기본값)")
    print("\n스레드 메모리는 파이썬 힙 밖의 스택이라 tracemalloc이 잡지 못해 비교에서 뺐다.")


if __name__ == "__main__":
    main()
