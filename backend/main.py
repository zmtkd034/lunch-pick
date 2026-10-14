"""오늘 뭐 먹지? API.

L01: 서버 동작 확인(/api/health).
L02: 식당 등록·목록(이름 검색, 음식 종류·가격대 필터). 데이터는 MariaDB에 저장한다.
L03: 식당 부분 수정·삭제·방문 기록(먹었어요).
L04: 조건(종류·가격대 여러 개, 최근 N일 방문 제외)에 맞는 식당 하나를 무작위 추천.
L09: 선호도(preference), 추천에서 별로 제외(exclude_disliked)·패스한 식당 제외(exclude_ids).
L11: 기본 메뉴 목록에서 메뉴 하나를 무작위 추천(종류 여러 개, 패스한 메뉴 제외).
L21: DB 오류는 서버 로그에 남기고, 연결 오류만 503·나머지는 500으로 응답한다.
L25: 회원가입·로그인·로그아웃·현재 사용자. 로그인 상태는 DB 세션과 HttpOnly 쿠키(lunch_pick_session)로 유지한다.
"""

import logging
import random
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.menus import MENUS
from backend.models import RestaurantRow, SessionRow, UserRow
from backend.schemas import (
    PASSWORD_MAX_LENGTH,
    Category,
    LoginRequest,
    Menu,
    PriceRange,
    Restaurant,
    RestaurantCreate,
    RestaurantUpdate,
    SignupRequest,
    User,
    VisitRequest,
    validate_date,
)
from backend.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    verify_dummy_password,
    verify_password,
)

app = FastAPI(title="Lunch Pick API")

EXCLUDE_DAYS_MAX = 30
# 패스한 식당 id는 화면에서 모아 보낸다. 요청이 지나치게 길어지지 않게 개수를 제한한다.
EXCLUDE_IDS_MAX = 100
# 같은 컴퓨터의 Task Flow(task_flow_session)와 섞이지 않게 쿠키 이름을 다르게 한다(L25).
SESSION_COOKIE = "lunch_pick_session"
SESSION_MAX_AGE = timedelta(days=7)
# 학습용 HTTP 주소에서도 동작하도록 Secure는 붙이지 않는다(API-SPEC 인증 참고).
SESSION_COOKIE_OPTIONS = {"path": "/api", "httponly": True, "samesite": "lax", "secure": False}


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


@app.exception_handler(RequestValidationError)
async def hide_auth_input(request: Request, exc: RequestValidationError) -> JSONResponse:
    # 인증 API의 422에는 보낸 값(input, 비밀번호 포함)을 되돌려 주지 않는다. 다른 API는 기본 형식 그대로다.
    if not request.url.path.startswith("/api/auth/"):
        return await request_validation_exception_handler(request, exc)
    errors = [{key: value for key, value in error.items() if key != "input"} for error in exc.errors()]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": jsonable_encoder(errors)})


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE)]


def _utc_now() -> datetime:
    # UTC 기준, 초 단위로 저장한다.
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _to_user(row: UserRow) -> User:
    return User(id=row.id, username=row.username, created_at=row.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"))


def _find_session(session: Session, token: str | None) -> SessionRow | None:
    # 만료된 세션은 없는 것으로 본다.
    if not token:
        return None
    return session.scalar(
        select(SessionRow).where(
            SessionRow.token_hash == hash_session_token(token), SessionRow.expires_at > _utc_now()
        )
    )


def get_current_user(session: SessionDep, token: SessionCookie = None) -> UserRow:
    found = _find_session(session, token)
    if found is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return session.get(UserRow, found.user_id)


CurrentUser = Annotated[UserRow, Depends(get_current_user)]


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


@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, session: SessionDep) -> User:
    # 가입만 하고 로그인은 하지 않는다(쿠키를 보내지 않음).
    username_taken = HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if session.scalar(select(UserRow.id).where(UserRow.username == payload.username)) is not None:
        raise username_taken
    row = UserRow(username=payload.username, password_hash=hash_password(payload.password), created_at=_utc_now())
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        # 같은 아이디로 동시에 가입한 경우 DB의 UNIQUE 제약이 막는다.
        session.rollback()
        raise username_taken from None
    return _to_user(row)


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response, session: SessionDep, token: SessionCookie = None) -> User:
    # 없는 아이디와 틀린 비밀번호를 같은 401로 응답한다(무엇이 틀렸는지 알려 주지 않는다).
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if len(payload.password) > PASSWORD_MAX_LENGTH:
        # 가입 규칙보다 긴 비밀번호는 맞을 수 없으므로 해시 계산 없이 거절한다.
        raise invalid
    user = session.scalar(select(UserRow).where(UserRow.username == payload.username))
    if user is None:
        verify_dummy_password(payload.password)
        raise invalid
    if not verify_password(payload.password, user.password_hash):
        raise invalid

    # 이미 로그인한 쿠키가 있으면 그 세션은 지우고 새 세션을 만든다.
    old = _find_session(session, token)
    if old is not None:
        session.delete(old)
    new_token = new_session_token()
    now = _utc_now()
    session.add(
        SessionRow(
            token_hash=hash_session_token(new_token), user_id=user.id, created_at=now, expires_at=now + SESSION_MAX_AGE
        )
    )
    session.commit()
    response.set_cookie(
        SESSION_COOKIE, new_token, max_age=int(SESSION_MAX_AGE.total_seconds()), **SESSION_COOKIE_OPTIONS
    )
    return _to_user(user)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(session: SessionDep, token: SessionCookie = None) -> Response:
    # 로그인하지 않았거나 이미 로그아웃했어도 204로 응답한다.
    if token:
        session.execute(delete(SessionRow).where(SessionRow.token_hash == hash_session_token(token)))
        session.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, **SESSION_COOKIE_OPTIONS)
    return response


@app.get("/api/auth/me")
def me(user: CurrentUser) -> User:
    return _to_user(user)


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
