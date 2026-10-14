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
- [x] L02: API-SPEC.md 작성, restaurants 테이블과 init 스크립트, 식당 등록(POST)·목록(GET, 검색·필터) API.
  확인: 정상 201, 빈 이름·51자·잘못된 종류·가격대·501자 메모 422, API 재시작 후 데이터 유지.
  - 변경 파일: API-SPEC.md(신규, L02~L04 전체 API 계약), backend/schemas.py(RestaurantCreate·Restaurant 검증), backend/models.py(restaurants 테이블), backend/init_db.py(없는 테이블만 생성), backend/main.py(GET·POST /api/restaurants, DB 연결 실패 503)
  - 실행 명령: .venv 활성화 후 python -m backend.init_db → python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload
  - 확인 결과(2026-10-14, HTTP 요청 자동 확인 42개 통과): init_db 1회차 생성·2회차 그대로. SHOW CREATE TABLE로 열·기본값·CHECK(종류·가격대·빈 이름)·utf8mb4_unicode_ci 확인. 처음 목록 [], 정상 등록 201(이름 공백 제거, last_visited_on null, created_at Z), 기본값 ETC·MID·"", 이름 50자·메모 500자 허용, HTML·%·_ 포함 이름 그대로 저장. 빈·공백·51자·누락·null·숫자 이름, 잘못된·소문자 종류, 잘못된 가격대, 메모 501자·null, id·created_at·last_visited_on·정의 안 된 필드 전송, 배열 본문, 깨진 JSON 422이며 저장 안 됨. 목록 등록 순서, 검색(한글·대소문자 무시·앞뒤 공백 제거·%·_ 글자 취급·빈 검색어 전체), category·price_range 필터와 AND, 결과 없음 [], 잘못된 필터 422. API를 재시작(PID 변경)해도 목록 그대로, id 이어서 발급. 잘못된 DB 포트로 띄운 임시 API는 목록 503 Database unavailable·health 200, 로그에 비밀번호 없음. 처음 확인 때 시험 스크립트의 기대 건수(8→7)가 틀려 2건 실패했고, 스크립트를 고친 뒤 데이터를 지우고 전체를 다시 확인했다. 시험 데이터 삭제 후 restaurants 0건·AUTO_INCREMENT 1.
  - 남은 오류: 없음. 수정·삭제·방문 기록은 L03, 추천은 L04에서 구현한다.
- [x] L03: 식당 수정(PATCH)·삭제(DELETE)·방문 기록(POST /visit) API.
  확인: 보내지 않은 필드 유지, 없는 id 404, 삭제 204, 방문 기록 시 last_visited_on 저장.
  - 변경 파일: backend/schemas.py(RestaurantUpdate 부분 수정 검증, VisitRequest 날짜 검증), backend/main.py(PATCH·DELETE /api/restaurants/{id}, POST /api/restaurants/{id}/visit)
  - 실행 명령: .venv 활성화 후 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload
  - 확인 결과(2026-10-14, HTTP 요청 자동 확인 46개 통과 + L02 회귀 40개 통과): 같은 이름 3개에서 category만 PATCH 시 나머지 필드·created_at 유지·다른 항목 불변, 여러 필드 동시 수정·이름 공백 제거·메모 비우기, {} 변경 없음, 50자·500자 허용. null 4종·빈·공백·51자 이름·501자 메모·잘못된 종류·가격대·id·created_at·last_visited_on·정의 안 된 필드·유효+무효 혼합·배열·깨진 JSON 422이며 일부도 적용 안 됨. 없는 id 404 Restaurant not found, 숫자 아닌 id 422. 방문 기록 200·last_visited_on 저장·다른 필드와 항목 불변·다시 기록하면 덮어씀(윤년 허용), 날짜 누락·null·없는 날짜·슬래시·한 자리 월·시간 포함·숫자·정의 안 된 필드 422이며 값 그대로, 없는 id 404. DELETE 204(본문 없음)·해당 항목만 삭제·순서 유지, 재삭제·삭제된 id PATCH·방문 404, 삭제된 id 재사용 안 함. 수정 후 필터 결과 반영. 시험 데이터 삭제 후 restaurants 0건.
  - 남은 오류: 없음. 미래 날짜 방문 기록은 막지 않는다(화면이 로컬 오늘 날짜를 보낸다).
- [x] L04: 추천 API(조건: 종류·가격대 여러 개, 최근 N일 제외).
  확인: 조건에 맞는 식당만 나옴(여러 번 호출), N일 제외 동작, 맞는 식당 없으면 404와 안내용 메시지.
  - 변경 파일: backend/main.py(GET /api/recommendation: 종류·가격대 여러 개 OR, 조건끼리 AND, exclude_days 0~30과 로컬 today 기준 최근 N일 방문 제외, DB에서 무작위 1건)
  - 실행 명령: .venv 활성화 후 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload
  - 확인 결과(2026-10-14, HTTP 요청 자동 확인 27개 통과 + L03 46개·L02 40개 회귀 통과): 방문일이 다른 식당 6개로 조건마다 150번씩 호출해 허용된 식당만 나오고 허용된 식당이 모두 한 번 이상 나옴(무작위). 조건 없음 전체, category 하나·여러 개, price_range 하나·여러 개, 종류·가격대 AND. today 2026-10-14 기준 exclude_days 0(제외 없음)·1(오늘 방문 제외)·7(6일 전까지 제외, 7일 전 포함)·8·30, 방문 기록 없는 곳은 항상 포함, 미래 날짜 방문은 범위 밖이라 포함, today를 바꾸면 기준도 바뀜. 식당 0개·조건 불일치·제외 후 없음 404 No matching restaurant. 잘못된·소문자 category, 잘못된 price_range, exclude_days 31·-1·문자, today 누락(N≥1)·없는 날짜·슬래시, N=0이어도 잘못된 today 422. 추천 호출은 데이터를 바꾸지 않음. 시험 데이터 삭제 후 restaurants 0건.
  - 남은 오류: 없음. 무작위는 DB의 RAND()로 고르며, 식당 수가 많지 않은 개인용 규모를 전제로 한다.
## 2장: React 화면
- [x] L05: React(Vite) 프로젝트 생성, 개발 서버에서 /api를 8100으로 전달, 식당 목록·등록 화면.
  확인: 화면 등록이 API·DB에 저장, 빈 이름 거절, HTML 글자 표시. (npm 필요: sudo apt install npm)
  - 변경 파일: frontend/(신규, npm create vite@9.2.1 --template react 후 예제 파일·이미지 삭제): vite.config.js(127.0.0.1:5173, /api → 127.0.0.1:8100 전달), index.html(한국어·제목), src/api.js(API 호출·오류 문구), src/constants.js(종류·가격대 이름, 입력 검증), src/components/RestaurantForm.jsx(등록 폼), src/components/RestaurantList.jsx(목록), src/App.jsx·App.css·index.css
  - 새 패키지(npm, frontend/package.json·package-lock.json): react·react-dom 19, vite 8, @vitejs/plugin-react 6, oxlint(코드 검사) — Vite React 템플릿 기본 구성. 사용자가 sudo apt install -y npm으로 npm 9.2.0 설치.
  - 실행 명령: 백엔드 .venv 활성화 후 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload / 화면 cd frontend && npm install(처음 한 번) && npm run dev → http://127.0.0.1:5173
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 21개 통과, npm run lint 경고 0, npm run build 성공): 5173에서 /api/health가 8100으로 전달됨. 처음 빈 목록 안내, 빈 이름·51자 이름 화면에서 거절(서버로 안 보냄, 입력값 유지). 등록 시 목록 표시·이름 공백 제거·배지(종류·가격대·방문 기록 없음)·메모, 입력칸 비움·선택칸 기본값 복귀, API 목록과 종류·가격대·메모 일치, 기본값 기타·보통. HTML 이름·메모 글자 표시(img·script 실행 안 됨). 빠르게 3번 제출해도 1건만 등록. 새로고침 후 목록·등록 순서 유지, 마지막 방문일 표시, 화면 목록 = API 목록. 백엔드 중지 시 "식당 목록을 불러오지 못했습니다" 배너(빈 목록 안내 대신)·등록 실패 안내·입력값 유지, 백엔드 재시작 후 다시 불러오기로 복구. 375px 가로 스크롤 없음, JS 오류 없음. 첫 확인에서 빠른 중복 제출 시 3건이 등록되는 문제를 발견해 useRef로 막도록 고친 뒤 데이터를 지우고 전체를 다시 확인했다. lint 경고(effect 안 setState)는 React 권장 방식(응답 콜백에서만 setState, 이전 응답 무시)으로 고쳤다. 시험 데이터 삭제 후 restaurants 0건.
  - 남은 오류: 없음. 수정·삭제·먹었어요·검색 필터 화면은 L06, 추천 화면은 L07에서 만든다.
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
