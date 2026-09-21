# async def vs def — FastAPI 엔드포인트 선언이 동시성에 미치는 영향

FastAPI에서 엔드포인트를 `def`로 쓸지 `async def`로 쓸지에 따라 서버가 어떻게 달라지는지
직접 재보는 PoC다. 무한루프 엔드포인트 하나가 서버 전체를 멈추는지, 워커 스레드가 언제
생기는지, uvloop이 결과를 바꾸는지를 각각 측정한다.

관련 글: [def와 async def는 무엇이 다른가: 커널까지 따라가 본 파이썬 웹 서버](https://techtaurant.com/post/01a0c1f6-c2fd-77d4-8178-42c12d9f90ac)

## 실행

모든 스크립트는 PEP 723 인라인 메타데이터를 달고 있어 별도 설치 없이 바로 돌아간다.

```bash
uv run measure_event_loop_blocking.py
```

의존성이 필요 없는 스크립트는 `python3`로도 돈다.

## 스크립트

| 파일 | 확인하는 것 | 걸리는 시간 |
| --- | --- | --- |
| `measure_event_loop_blocking.py` | 블로킹 엔드포인트가 다른 요청을 막는지, 루프 구현별로 다른지 | 약 60초 |
| `measure_worker_thread_count.py` | 워커 스레드가 `async def` 때문에 생기는지 `def` 때문에 생기는지 | 약 15초 |
| `measure_thread_pool_exhaustion.py` | 워커 40개가 CPU를 태울 때 나머지 엔드포인트가 받는 영향 | 약 35초 |
| `measure_wsgi_blocking.py` | 동기 파이썬(WSGI)에서도 같은 현상이 생기는지 | 약 25초 |
| `measure_coroutine_cost.py` | 코루틴 1만 개와 스레드 1만 개의 생성 비용 | 약 2초 |
| `inspect_coroutine_in_worker_thread.py` | 코루틴 함수를 워커 스레드에 넘기면 생기는 일 | 1초 미만 |

`blocking_app.py`와 `thread_count_app.py`는 측정 대상 FastAPI 앱이고,
`measurement_server.py`는 세 측정 스크립트가 공유하는 uvicorn 기동과 HTTP 조회다.

진짜 무한루프는 서버를 죽여야만 끝나므로 10초짜리 바쁜 대기로 바꿨다. 관측 시점인 0.5초에서는
둘이 구별되지 않는다.

## 측정 결과

아래는 측정 환경에서 나온 값이다. 절대 수치는 머신에 따라 달라지지만 대소 관계는 유지된다.

### 블로킹 엔드포인트가 다른 요청을 막는가

`/add`는 `1 + 1`만 돌려주는 엔드포인트다. 블로킹 요청을 보낸 0.5초 뒤에 호출했다.

| 루프 | 블로킹 엔드포인트 | `/add` 지연 |
| --- | --- | --- |
| uvloop | `async def` + 순수 busy loop | 9.50초 |
| uvloop | `def` + 순수 busy loop | 0.03초 |
| uvloop | `async def` + `await` 양보 | 0.00초 |
| asyncio | `async def` + 순수 busy loop | 9.50초 |
| asyncio | `def` + 순수 busy loop | 0.04초 |

9.50초는 블로킹 작업이 끝날 때까지 통째로 기다렸다는 뜻이다. uvloop과 표준 asyncio의 값이
같다는 점, 그리고 `await asyncio.sleep(0)` 한 줄을 넣은 세 번째 줄이 0.00초라는 점이 핵심이다.

### 워커 스레드는 언제 생기는가

| 시점 | 전체 스레드 | anyio 워커 |
| --- | ---: | ---: |
| 기동 직후 | 1 | 0 |
| `async def` 엔드포인트 50회 호출 뒤 | 1 | 0 |
| `def` 엔드포인트 8개 동시 호출 뒤 | 9 | 8 |

### 워커가 CPU를 태우면

| 상황 | `async def` `/add` | `def` `/add-sync` |
| --- | --- | --- |
| 블로커 없음 | 0.00초 | 0.03초 |
| CPU busy `def` 40개 실행 중 | 11.87초 | 14.41초 |

`def`로 격리해도 CPU 바운드 작업에서는 GIL 경합과 토큰 고갈로 전부 느려진다.

### 동기 파이썬(WSGI)은 어떤가

| WSGI 서버 | `/add` 지연 |
| --- | --- |
| 단일 스레드 순차 처리 | 9.51초 |
| 요청마다 스레드 | 0.06초 |

숫자가 ASGI 쪽과 판박이다. 기준은 `async`냐 `sync`냐보다 그 요청이 남의 실행 흐름을
점유하는지 여부에 가깝다.

### 코루틴과 스레드의 비용

| | 코루틴 | 스레드 |
| --- | --- | --- |
| 1만 개 생성 및 실행 | 93.0ms | 601.6ms |
| 객체 하나 | 184바이트 | OS 스택 예약 |

스레드 메모리는 파이썬 힙 밖의 스택이라 `tracemalloc`이 잡지 못해 비교에서 뺐다.

### 코루틴 함수를 워커 스레드에 넘기면

```
[1] 스레드에서 async 함수를 호출한 결과 : coroutine -> <coroutine object compute at 0x103233880>
[2] to_thread.run_sync(동기 함수)  : int -> 42
[3] to_thread.run_sync(async 함수) : coroutine -> <coroutine object compute at 0x103233f40>
[4] 워커 스레드에서 본 이벤트 루프 : 없음 (no running event loop)
```

워커 스레드가 하는 일은 그냥 호출이라 async 함수를 넘기면 코루틴 객체만 돌아온다. 실행하려면
이벤트 루프가 필요한데 워커 스레드에는 루프가 없다.

## 측정 환경

macOS, Python 3.13.5, FastAPI 0.141.1, uvicorn 0.53.0, uvloop 0.22.1, anyio 4.15.1.
uvicorn은 단일 프로세스로 띄웠고 GIL 스위치 간격은 기본값 5ms다.
