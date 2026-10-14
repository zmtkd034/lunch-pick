"""오늘 뭐 먹지? API.

L01: 서버 동작 확인(/api/health).
L02: 식당 등록·목록(이름 검색, 음식 종류·가격대 필터). 데이터는 MariaDB에 저장한다.
"""

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import RestaurantRow
from backend.schemas import Category, PriceRange, Restaurant, RestaurantCreate

app = FastAPI(title="Lunch Pick API")


@app.exception_handler(OperationalError)
def database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
    # DB에 연결하지 못하면 내부 오류 내용(접속 정보 등)을 숨기고 503으로 알린다.
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "Database unavailable"})


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def _utc_now() -> datetime:
    # UTC 기준, 초 단위로 저장한다.
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _to_restaurant(row: RestaurantRow) -> Restaurant:
    return Restaurant(
        id=row.id,
        name=row.name,
        category=row.category,
        price_range=row.price_range,
        memo=row.memo,
        last_visited_on=row.last_visited_on.isoformat() if row.last_visited_on else None,
        created_at=row.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/restaurants")
def list_restaurants(
    session: SessionDep,
    q: str | None = None,
    category: Category | None = None,
    price_range: PriceRange | None = None,
) -> list[Restaurant]:
    # 이름 검색·음식 종류·가격대를 모두 만족하는 식당만 등록 순서대로 돌려준다(AND).
    query = select(RestaurantRow).order_by(RestaurantRow.id)
    keyword = (q or "").strip()
    if keyword:
        # 테이블 정렬 규칙(utf8mb4_unicode_ci)이 대소문자를 구분하지 않는다. %, _는 글자로 찾는다.
        query = query.where(RestaurantRow.name.contains(keyword, autoescape=True))
    if category is not None:
        query = query.where(RestaurantRow.category == category)
    if price_range is not None:
        query = query.where(RestaurantRow.price_range == price_range)
    return [_to_restaurant(row) for row in session.scalars(query)]


@app.post("/api/restaurants", status_code=status.HTTP_201_CREATED)
def create_restaurant(payload: RestaurantCreate, session: SessionDep) -> Restaurant:
    row = RestaurantRow(
        name=payload.name,
        category=payload.category,
        price_range=payload.price_range,
        memo=payload.memo,
        created_at=_utc_now(),
    )
    session.add(row)
    session.commit()
    return _to_restaurant(row)
