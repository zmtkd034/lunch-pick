"""요청·응답 데이터 형식과 입력 검증 규칙(API-SPEC.md의 Restaurant)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

NAME_MAX_LENGTH = 50
MEMO_MAX_LENGTH = 500

Category = Literal["KOREAN", "CHINESE", "JAPANESE", "WESTERN", "SNACK", "ETC"]
PriceRange = Literal["LOW", "MID", "HIGH"]


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

    _normalize_name = field_validator("name")(normalize_name)


class Restaurant(BaseModel):
    id: int
    name: str
    category: Category
    price_range: PriceRange
    memo: str
    last_visited_on: str | None
    created_at: str
