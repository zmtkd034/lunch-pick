"""restaurants 테이블을 만든다. 실행: python -m backend.init_db

이미 있는 테이블은 그대로 두며, 기존 데이터를 지우거나 초기화하지 않는다.
L09: 기존 테이블에 preference 열이 없으면 추가한다(ALTER TABLE ADD COLUMN, 기존 행은 NULL).
"""

from sqlalchemy import inspect, text

from backend.database import Base, engine
from backend.models import RestaurantRow

# 열과 CHECK 제약을 한 문장으로 추가한다. 기존 행은 선호도 미지정(NULL)으로 남는다.
ADD_PREFERENCE = text(
    "ALTER TABLE restaurants"
    " ADD COLUMN preference VARCHAR(10) NULL AFTER memo,"
    " ADD CONSTRAINT ck_restaurants_preference CHECK (preference IN ('LIKE', 'SOSO', 'DISLIKE'))"
)


def main() -> None:
    table_name = RestaurantRow.__tablename__
    existed = inspect(engine).has_table(table_name)
    # create_all은 없는 테이블만 만든다(CREATE TABLE만 실행, DROP 없음).
    Base.metadata.create_all(engine)
    if existed:
        print(f"'{table_name}' 테이블이 이미 있어 그대로 두었습니다.")
    else:
        print(f"'{table_name}' 테이블을 만들었습니다.")

    columns = {column["name"] for column in inspect(engine).get_columns(table_name)}
    if "preference" in columns:
        print("'restaurants.preference' 열이 이미 있어 그대로 두었습니다.")
    else:
        with engine.begin() as connection:
            connection.execute(ADD_PREFERENCE)
        print("'restaurants.preference' 열을 추가했습니다. 기존 식당은 선호도 미지정(NULL)입니다.")


if __name__ == "__main__":
    main()
