"""restaurants 테이블을 만든다. 실행: python -m backend.init_db

이미 있는 테이블은 그대로 두며, 기존 데이터를 지우거나 초기화하지 않는다.
"""

from sqlalchemy import inspect

from backend.database import Base, engine
from backend.models import RestaurantRow


def main() -> None:
    table_name = RestaurantRow.__tablename__
    existed = inspect(engine).has_table(table_name)
    # create_all은 없는 테이블만 만든다(CREATE TABLE만 실행, DROP 없음).
    Base.metadata.create_all(engine)
    if existed:
        print(f"'{table_name}' 테이블이 이미 있어 그대로 두었습니다.")
    else:
        print(f"'{table_name}' 테이블을 만들었습니다.")


if __name__ == "__main__":
    main()
