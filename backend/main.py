"""오늘 뭐 먹지? API.

L01: 서버 동작 확인(/api/health).
L02: 식당 등록·목록(이름 검색, 음식 종류·가격대 필터). 데이터는 MariaDB에 저장한다.
L03: 식당 부분 수정·삭제·방문 기록(먹었어요).
L04: 조건(종류·가격대 여러 개, 최근 N일 방문 제외)에 맞는 식당 하나를 무작위 추천.
L09: 선호도(preference), 추천에서 별로 제외(exclude_disliked)·패스한 식당 제외(exclude_ids).
L11: 기본 메뉴 목록에서 메뉴 하나를 무작위 추천(종류 여러 개, 패스한 메뉴 제외).
L21: DB 오류는 서버 로그에 남기고, 연결 오류만 503·나머지는 500으로 응답한다.
"""

import logging
import random
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.menus import MENUS
from backend.models import RestaurantRow
from backend.schemas import (
    Category,
    Menu,
    PriceRange,
    Restaurant,
    RestaurantCreate,
    RestaurantUpdate,
    VisitRequest,
    validate_date,
)

app = FastAPI(title="Lunch Pick API")

EXCLUDE_DAYS_MAX = 30
# 패스한 식당 id는 화면에서 모아 보낸다. 요청이 지나치게 길어지지 않게 개수를 제한한다.
EXCLUDE_IDS_MAX = 100


logger = logging.getLogger("uvicorn.error")

# 연결·접속 실패로 보는 MariaDB/PyMySQL 오류 번호. 이때만 503(DB에 연결할 수 없음)으로 알린다.
# 1044·1045 접속 권한/비밀번호, 1049 DB 없음, 2002·2003 서버에 연결 못함, 2006·2013 연결 끊김.
DB_CONNECTION_ERROR_CODES = {1044, 1045, 1049, 2002, 2003, 2006, 2013}


@app.exception_handler(DBAPIError)
def database_error(request: Request, exc: DBAPIError) -> JSONResponse:
    # 응답에는 내부 오류 내용(접속 정보·SQL)을 보여 주지 않고, 서버 로그에만 원인을 남긴다.
    # 로그에는 드라이버 오류(번호와 메시지)만 쓰고 SQL 문장과 값은 쓰지 않는다. 비밀번호는 오류 메시지에 들어가지 않는다.
    args = getattr(exc.orig, "args", ())
    code = args[0] if args and isinstance(args[0], int) else None
    logger.error("DB 오류 %s %s: %s %r", request.method, request.url.path, type(exc.orig).__name__, args)
    if exc.connection_invalidated or code in DB_CONNECTION_ERROR_CODES:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "Database unavailable"})
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})


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
        preference=row.preference,
        last_visited_on=row.last_visited_on.isoformat() if row.last_visited_on else None,
        created_at=row.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _get_row(session: Session, restaurant_id: int) -> RestaurantRow:
    row = session.get(RestaurantRow, restaurant_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return row


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
        preference=payload.preference,
        created_at=_utc_now(),
    )
    session.add(row)
    session.commit()
    return _to_restaurant(row)


@app.patch("/api/restaurants/{restaurant_id}")
def update_restaurant(restaurant_id: int, payload: RestaurantUpdate, session: SessionDep) -> Restaurant:
    row = _get_row(session, restaurant_id)
    # 보낸 필드만 바꾸고 보내지 않은 필드는 그대로 둔다.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    session.commit()
    return _to_restaurant(row)


@app.delete("/api/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(restaurant_id: int, session: SessionDep) -> Response:
    session.delete(_get_row(session, restaurant_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/restaurants/{restaurant_id}/visit")
def visit_restaurant(restaurant_id: int, payload: VisitRequest, session: SessionDep) -> Restaurant:
    # 보낸 날짜를 마지막 방문일로 저장한다.
    row = _get_row(session, restaurant_id)
    row.last_visited_on = date.fromisoformat(payload.visited_on)
    session.commit()
    return _to_restaurant(row)


@app.get("/api/recommendation")
def recommend(
    session: SessionDep,
    category: Annotated[list[Category] | None, Query()] = None,
    price_range: Annotated[list[PriceRange] | None, Query()] = None,
    exclude_days: Annotated[int, Query(ge=0, le=EXCLUDE_DAYS_MAX)] = 0,
    today: str | None = None,
    exclude_disliked: bool = False,
    exclude_ids: Annotated[list[int] | None, Query(max_length=EXCLUDE_IDS_MAX)] = None,
) -> Restaurant:
    # today는 사용자 PC의 로컬 날짜다. 보냈으면 항상 검사한다.
    local_today = None
    if today is not None:
        try:
            local_today = date.fromisoformat(validate_date(today))
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from None
    if exclude_days > 0 and local_today is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="today is required when exclude_days > 0"
        )

    # 종류·가격대는 여러 개 중 하나라도 맞으면 되고(OR), 조건끼리는 AND다. 주지 않으면 조건 없음.
    query = select(RestaurantRow)
    if category:
        query = query.where(RestaurantRow.category.in_(category))
    if price_range:
        query = query.where(RestaurantRow.price_range.in_(price_range))
    if exclude_days > 0:
        # 최근 N일(오늘 포함): today - (N - 1)일부터 today까지.
        since = local_today - timedelta(days=exclude_days - 1)
        # 방문 기록이 없거나, 최근 N일 범위 밖에 방문한 식당만 남긴다.
        query = query.where(
            or_(
                RestaurantRow.last_visited_on.is_(None),
                RestaurantRow.last_visited_on < since,
                RestaurantRow.last_visited_on > local_today,
            )
        )
    if exclude_disliked:
        # 선호도 미지정(NULL)은 별로가 아니므로 남긴다.
        query = query.where(or_(RestaurantRow.preference.is_(None), RestaurantRow.preference != "DISLIKE"))
    if exclude_ids:
        # 이번에 패스한 식당은 뺀다.
        query = query.where(RestaurantRow.id.not_in(exclude_ids))
    row = session.scalars(query.order_by(func.rand()).limit(1)).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching restaurant")
    return _to_restaurant(row)


@app.get("/api/menu-recommendation")
def recommend_menu(
    category: Annotated[list[Category] | None, Query()] = None,
    exclude_ids: Annotated[list[int] | None, Query(max_length=EXCLUDE_IDS_MAX)] = None,
) -> Menu:
    # 기본 메뉴 목록에서 고른 종류(여러 개 중 하나라도 맞으면 됨)의 메뉴를 무작위로 하나 고른다. DB는 쓰지 않는다.
    excluded = set(exclude_ids or [])
    candidates = [
        menu for menu in MENUS if (not category or menu.category in category) and menu.id not in excluded
    ]
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching menu")
    return random.choice(candidates)
