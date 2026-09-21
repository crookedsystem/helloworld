"""블로킹 엔드포인트가 이벤트 루프를 막는지 재보기 위한 최소 앱."""

import asyncio
import time

from fastapi import FastAPI

# 진짜 무한루프는 서버를 죽여야만 끝나므로, 같은 성질을 유지하면서 스스로 끝나도록
# 10초짜리 바쁜 대기로 바꿨다. 관측 시점(0.5초)에서는 무한루프와 구별되지 않는다.
BUSY_SECONDS = 10.0

app = FastAPI()


@app.get("/busy-async")
async def busy_async() -> dict[str, str]:
    deadline = time.monotonic() + BUSY_SECONDS
    while time.monotonic() < deadline:
        pass
    return {"done": "async"}


@app.get("/busy-sync")
def busy_sync() -> dict[str, str]:
    deadline = time.monotonic() + BUSY_SECONDS
    while time.monotonic() < deadline:
        pass
    return {"done": "sync"}


@app.get("/busy-async-yield")
async def busy_async_yield() -> dict[str, str]:
    deadline = time.monotonic() + BUSY_SECONDS
    while time.monotonic() < deadline:
        await asyncio.sleep(0)  # 매 바퀴 제어권을 루프에 돌려준다
    return {"done": "yield"}


@app.get("/add")
async def add() -> dict[str, int]:
    return {"result": 1 + 1}


@app.get("/add-sync")
def add_sync() -> dict[str, int]:
    return {"result": 1 + 1}
