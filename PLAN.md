# 오늘 뭐 먹지? PLAN
## 작업 원칙
한 번에 아래 작업 하나만 구현한다. 실제 확인 전에는 완료로 표시하지 않는다.
상태는 [ ] 미완료, [x] 확인 완료로 관리하고 확인 결과를 각 항목 아래 기록한다.
포트: API 8100, 화면 개발 서버 5173(Task Flow의 80·8000·8001과 겹치지 않게 한다).
## 1장: 백엔드와 DB
- [x] L01: 이 프로젝트 전용 MariaDB DB·계정, .env/.env.example, FastAPI /api/health와 DB SELECT 1 확인.
  확인: curl로 /api/health 200, DB 접속 성공. .env가 Git에서 제외된다.
  - 변경 파일: .gitignore, .env.example(가짜 값), requirements.txt, backend/__init__.py, backend/database.py(.env 읽기·엔진·세션), backend/check_db.py(접속 확인), backend/main.py(/api/health). .env는 사용자가 직접 작성(Git 제외, 권한 600).
  - 준비: python3 -m venv .venv, pip install fastapi uvicorn sqlalchemy pymysql python-dotenv (fastapi 0.143.0, uvicorn 0.54.0, SQLAlchemy 2.1.4, PyMySQL 1.2.3, python-dotenv 1.2.4), pip freeze > requirements.txt
  - 준비(사용자, sudo mariadb): CREATE DATABASE lunch_pick(utf8mb4, utf8mb4_unicode_ci), CREATE USER 'lunch_pick_app'@'localhost', GRANT ALL PRIVILEGES ON lunch_pick.*
  - 실행 명령: .venv 활성화 후 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload / DB 확인: python -m backend.check_db
  - 확인 결과(2026-10-14): curl /api/health → 200 {"status":"ok"}, /docs 200. check_db: SELECT 1 → 1, 접속 계정 lunch_pick_app@localhost, DB lunch_pick, utf8mb4. 권한은 lunch_pick.*만, Task Flow DB(task_flow.tasks) 접근 거절(1142). engine URL 출력 시 비밀번호 가림. git check-ignore로 .env 제외 확인. 처음 접속은 1045(비밀번호 불일치)였고 사용자가 ALTER USER로 .env와 맞춘 뒤 성공. Task Flow(8001·localhost) 영향 없음.
  - 남은 오류: 없음. 권장: DB 비밀번호가 12자 미만이라 12자 이상으로 바꾸는 것을 권장한다(ALTER USER 후 .env도 같이 수정).
- [ ] L02: API-SPEC.md 작성, restaurants 테이블과 init 스크립트, 식당 등록(POST)·목록(GET, 검색·필터) API.
  확인: 정상 201, 빈 이름·51자·잘못된 종류·가격대·501자 메모 422, API 재시작 후 데이터 유지.
- [ ] L03: 식당 수정(PATCH)·삭제(DELETE)·방문 기록(POST /visit) API.
  확인: 보내지 않은 필드 유지, 없는 id 404, 삭제 204, 방문 기록 시 last_visited_on 저장.
- [ ] L04: 추천 API(조건: 종류·가격대 여러 개, 최근 N일 제외).
  확인: 조건에 맞는 식당만 나옴(여러 번 호출), N일 제외 동작, 맞는 식당 없으면 404와 안내용 메시지.
## 2장: React 화면
- [ ] L05: React(Vite) 프로젝트 생성, 개발 서버에서 /api를 8100으로 전달, 식당 목록·등록 화면.
  확인: 화면 등록이 API·DB에 저장, 빈 이름 거절, HTML 글자 표시. (npm 필요: sudo apt install npm)
- [ ] L06: 검색·필터, 수정·삭제(확인 창)·"먹었어요" 화면.
  확인: 필터 중 정확한 항목 수정·삭제, 삭제 취소 시 유지, 방문일 표시.
- [ ] L07: 추천 화면(조건 선택 + 카드 뽑기 애니메이션 + 결과에서 "먹었어요").
  확인: 조건에 맞는 결과만, 없으면 안내, 애니메이션 후 결과 표시, 375px 화면 가로 스크롤 없음.
## 3장: 실행 구성
- [ ] L08: 화면 빌드본(npm run build) 제공 방식과 실행 명령 정리(개발 서버 한 대, 계층별 역할 분리).
  확인: 빌드본 화면에서 등록·추천 동작, 실행 명령을 문서로 재현 가능.
## 실행 기준
작업마다 실제 존재하는 파일을 확인한 뒤 실행 명령을 기록한다.
## 기록
각 작업에 변경 파일, 실행 명령, 실제 확인 결과, 남은 오류를 기록한다.
정상 동작을 확인한 작업 단위로 Git 커밋한다.
