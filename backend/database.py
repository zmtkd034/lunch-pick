"""MariaDB 접속 설정.

접속 정보는 프로젝트 루트의 .env에서 읽는다(.env.example 참고). 비밀번호는 코드와 로그에 남기지 않는다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]

# 이미 설정된 환경 변수가 있으면 그 값을 우선한다.
load_dotenv(PROJECT_ROOT / ".env")


def _read_settings() -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"DB 접속 환경 변수가 없습니다: {', '.join(missing)}. "
            ".env.example을 참고해 프로젝트 루트의 .env를 확인하세요."
        )
    return {name: os.environ[name] for name in REQUIRED_ENV_VARS}


def _build_url() -> URL:
    settings = _read_settings()
    # URL.create는 비밀번호의 특수문자를 안전하게 처리하고, 출력할 때 비밀번호를 가린다.
    return URL.create(
        "mysql+pymysql",
        username=settings["DB_USER"],
        password=settings["DB_PASSWORD"],
        host=settings["DB_HOST"],
        port=int(settings["DB_PORT"]),
        database=settings["DB_NAME"],
        query={"charset": "utf8mb4"},
    )


# pool_pre_ping: 오래 쉬어 끊긴 연결을 사용 전에 확인해 다시 연결한다.
engine = create_engine(_build_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
