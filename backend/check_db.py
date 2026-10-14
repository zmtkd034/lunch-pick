"""DB 접속 확인. 실행: python -m backend.check_db

SELECT 1과 접속 계정·DB 이름·문자셋만 출력한다. 비밀번호는 출력하지 않는다.
"""

from sqlalchemy import text

from backend.database import engine


def main() -> None:
    with engine.connect() as connection:
        one = connection.execute(text("SELECT 1")).scalar()
        user, database, charset = connection.execute(
            text("SELECT CURRENT_USER(), DATABASE(), @@character_set_database")
        ).one()
    print(f"SELECT 1 → {one}")
    print(f"접속 계정: {user}, DB: {database}, 문자셋: {charset}")


if __name__ == "__main__":
    main()
