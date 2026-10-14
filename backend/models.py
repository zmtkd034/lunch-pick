"""DB 테이블 정의. 필드 규칙은 API-SPEC.md의 Restaurant와 같다."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base
from backend.schemas import MEMO_MAX_LENGTH, NAME_MAX_LENGTH


class RestaurantRow(Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        # API 검증과 별개로 DB에도 허용 값을 걸어 둔다.
        CheckConstraint(
            "category IN ('KOREAN', 'CHINESE', 'JAPANESE', 'WESTERN', 'SNACK', 'ETC')",
            name="ck_restaurants_category",
        ),
        CheckConstraint("price_range IN ('LOW', 'MID', 'HIGH')", name="ck_restaurants_price_range"),
        CheckConstraint("CHAR_LENGTH(TRIM(name)) > 0", name="ck_restaurants_name_not_blank"),
        CheckConstraint("preference IN ('LIKE', 'SOSO', 'DISLIKE')", name="ck_restaurants_preference"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    category: Mapped[str] = mapped_column(String(10), nullable=False, default="ETC", server_default="ETC")
    price_range: Mapped[str] = mapped_column(String(10), nullable=False, default="MID", server_default="MID")
    memo: Mapped[str] = mapped_column(String(MEMO_MAX_LENGTH), nullable=False, default="", server_default="")
    # 선호도(L09). 미지정은 NULL.
    preference: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_visited_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    # UTC 기준 등록 시각. API 응답에서는 ISO 8601(끝에 Z)로 바꾼다.
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
