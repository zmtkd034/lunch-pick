"""오늘 뭐 먹지? 테이블을 만든다. 실행: python -m backend.init_db

이미 있는 테이블은 그대로 두며, 기존 데이터를 지우거나 초기화하지 않는다.
L09: 기존 restaurants에 preference 열이 없으면 추가한다(ALTER TABLE ADD COLUMN, 기존 행은 NULL).
L24: users·sessions 테이블을 만들고, restaurants에 user_id 열이 없으면 추가한다(기존 행은 주인 없음 NULL).
"""

from sqlalchemy import inspect, text

from backend.database import Base, engine
from backend.models import RestaurantRow, SessionRow, UserRow

# 열과 제약을 한 문장으로 추가한다. 기존 행은 NULL로 남는다(DROP·TRUNCATE 없음).
ADD_COLUMNS = {
    "preference": text(
        "ALTER TABLE restaurants"
        " ADD COLUMN preference VARCHAR(10) NULL AFTER memo,"
        " ADD CONSTRAINT ck_restaurants_preference CHECK (preference IN ('LIKE', 'SOSO', 'DISLIKE'))"
    ),
    "user_id": text(
        "ALTER TABLE restaurants"
        " ADD COLUMN user_id INT NULL AFTER id,"
        " ADD INDEX ix_restaurants_user_id (user_id),"
        " ADD CONSTRAINT fk_restaurants_user_id FOREIGN KEY (user_id) REFERENCES users (id)"
    ),
}


def main() -> None:
    table_names = [UserRow.__tablename__, SessionRow.__tablename__, RestaurantRow.__tablename__]
    existed = {name: inspect(engine).has_table(name) for name in table_names}
    # create_all은 없는 테이블만 만든다(CREATE TABLE만 실행, DROP 없음). users가 먼저 있어야 외래 키를 걸 수 있다.
    Base.metadata.create_all(engine)
    for name in table_names:
        if existed[name]:
            print(f"'{name}' 테이블이 이미 있어 그대로 두었습니다.")
        else:
            print(f"'{name}' 테이블을 만들었습니다.")

    for column, statement in ADD_COLUMNS.items():
        columns = {item["name"] for item in inspect(engine).get_columns(RestaurantRow.__tablename__)}
        if column in columns:
            print(f"'restaurants.{column}' 열이 이미 있어 그대로 두었습니다.")
        else:
            with engine.begin() as connection:
                connection.execute(statement)
            print(f"'restaurants.{column}' 열을 추가했습니다. 기존 식당은 NULL로 남습니다.")


if __name__ == "__main__":
    main()
