"""요청·응답 데이터 형식과 입력 검증 규칙(API-SPEC.md의 Restaurant·User)."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

NAME_MAX_LENGTH = 50
MEMO_MAX_LENGTH = 500
USERNAME_PATTERN = r"^[a-z0-9]{4,20}$"
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# MariaDB DATE가 보장하는 범위의 시작(L21). 이보다 이른 날짜는 저장·날짜 계산에서 오류가 날 수 있어 받지 않는다.
DATE_MIN_YEAR = 1000

Category = Literal["KOREAN", "CHINESE", "JAPANESE", "WESTERN", "SNACK", "ETC"]
PriceRange = Literal["LOW", "MID", "HIGH"]
# 선호도. 미지정은 None(null).
Preference = Literal["LIKE", "SOSO", "DISLIKE"]


def normalize_name(value: str) -> str:
    name = value.strip()
    if not 1 <= len(name) <= NAME_MAX_LENGTH:
        raise ValueError(f"name must be 1-{NAME_MAX_LENGTH} characters after trimming")
    return name


class RestaurantCreate(BaseModel):
    # 정의되지 않은 필드(id, created_at, last_visited_on 포함)는 거절한다.
    model_config = ConfigDict(extra="forbid")

    name: str
    category: Category = "ETC"
    price_range: PriceRange = "MID"
    memo: str = Field(default="", max_length=MEMO_MAX_LENGTH)
    preference: Preference | None = None

    _normalize_name = field_validator("name")(normalize_name)


def validate_date(value: str) -> str:
    # 실제 존재하는 YYYY-MM-DD 날짜만 받는다(예: 2026-02-30 거절).
    if not DATE_PATTERN.fullmatch(value):
        raise ValueError("date must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError("date must be a real calendar date") from None
    if parsed.year < DATE_MIN_YEAR:
        raise ValueError(f"date must be between {DATE_MIN_YEAR}-01-01 and 9999-12-31")
    return value


class RestaurantUpdate(BaseModel):
    """부분 수정. 보낸 필드만 바꾸고 보내지 않은 필드는 그대로 둔다(model_fields_set으로 구분)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    category: Category | None = None
    price_range: PriceRange | None = None
    memo: str | None = Field(default=None, max_length=MEMO_MAX_LENGTH)
    # preference는 null을 보내면 선호도를 지운다(다른 필드와 달리 null 허용).
    preference: Preference | None = None

    # 기본값은 검증하지 않으므로, 이 검증은 값을 실제로 보냈을 때만 실행된다.
    @field_validator("name", "category", "price_range", "memo")
    @classmethod
    def reject_null(cls, value, info):
        if value is None:
            raise ValueError(f"{info.field_name} cannot be null")
        return value

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return normalize_name(value)


class VisitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 사용자 PC의 로컬 날짜를 화면이 보낸다.
    visited_on: str

    _validate_visited_on = field_validator("visited_on")(validate_date)


class Menu(BaseModel):
    # 기본 메뉴(L11). 앱이 제공하는 고정 목록이다.
    id: int
    name: str
    category: Category


class Restaurant(BaseModel):
    id: int
    name: str
    category: Category
    price_range: PriceRange
    memo: str
    preference: Preference | None
    last_visited_on: str | None
    created_at: str


class SignupRequest(BaseModel):
    # 아이디는 공백 제거·소문자 변환 없이 그대로 검사한다. 비밀번호는 앞뒤 공백도 비밀번호로 본다(L25).
    model_config = ConfigDict(extra="forbid")

    username: str = Field(pattern=USERNAME_PATTERN)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class LoginRequest(BaseModel):
    # 아이디·비밀번호 규칙은 검사하지 않는다. 규칙에 맞지 않아도 422가 아니라 로그인 실패(401)로 처리한다.
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class User(BaseModel):
    # 비밀번호와 해시는 응답에 넣지 않는다.
    id: int
    username: str
    created_at: str
