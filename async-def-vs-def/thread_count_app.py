"""요청 종류에 따라 워커 스레드가 생기는지 세어보기 위한 앱."""

import threading
import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/threads")
async def threads() -> dict[str, object]:
    names = sorted(t.name for t in threading.enumerate())
    return {
        "total": threading.active_count(),
        "anyio_workers": sum(1 for n in names if "AnyIO worker" in n),
        "names": names,
    }


@app.get("/async-work")
async def async_work() -> dict[str, str]:
    return {"kind": "async"}


@app.get("/sync-work")
def sync_work() -> dict[str, str]:
    time.sleep(0.3)  # 워커를 잠시 붙들어 동시에 여러 개가 뜨게 한다
    return {"kind": "sync"}
