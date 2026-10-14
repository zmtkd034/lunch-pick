"""오늘 뭐 먹지? API.

L01: 서버 동작 확인(/api/health). 식당 API는 L02부터 추가한다.
"""

from fastapi import FastAPI

app = FastAPI(title="Lunch Pick API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
