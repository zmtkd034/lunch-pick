# 오늘 뭐 먹지? PLAN
## 작업 원칙
한 번에 아래 작업 하나만 구현한다. 실제 확인 전에는 완료로 표시하지 않는다.
상태는 [ ] 미완료, [x] 확인 완료로 관리하고 확인 결과를 각 항목 아래 기록한다.
포트: API 8100, 화면 개발 서버 5173, 화면 빌드본 4173(L08부터)(Task Flow의 80·8000·8001과 겹치지 않게 한다).
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
- [x] L06: 검색·필터, 수정·삭제(확인 창)·"먹었어요" 화면.
  확인: 필터 중 정확한 항목 수정·삭제, 삭제 취소 시 유지, 방문일 표시.
  - 변경 파일: frontend/src/components/RestaurantFilters.jsx(신규, 이름 검색·종류·가격대 필터), frontend/src/components/RestaurantEditForm.jsx(신규, 수정 폼), frontend/src/components/RestaurantList.jsx(먹었어요·수정·삭제 버튼, 수정 중·요청 중 상태), frontend/src/App.jsx(PATCH·DELETE·visit 호출, 404 시 목록 다시 불러오기와 안내), frontend/src/constants.js(getLocalToday, matchesFilters), frontend/src/App.css
  - 실행 명령: 백엔드 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload / 화면 cd frontend && npm run dev → http://127.0.0.1:5173
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 24개 통과 + L05 21개 회귀 통과, lint 경고 0, build 성공): 같은 이름 식당 3개로 이름 검색·대소문자 무시·공백 제거, 종류·가격대 필터, 세 조건 AND, 결과 없음 안내. 필터(종류·가격대) 중 수정 폼에 기존 값, 빈 이름 거절(서버로 안 보냄), 취소 시 원래 값, 저장 시 해당 id에만 반영·다른 항목 불변·폼 닫힘·필터 유지·HTML 메모 글자 표시. 먹었어요 → 로컬 오늘 날짜가 해당 id에만 저장·방문일 표시. 필터 중 삭제 취소 시 유지, 확인 창에 이름 표시, 확인 시 해당 id만 삭제. 다른 곳에서 삭제된 항목 먹었어요·수정 저장 → 404 안내·목록 새로 불러옴·폼 닫힘. API 중지 시 수정 실패 안내·입력값 유지, 먹었어요 실패 배너, 실패한 요청은 DB 불변. 375px 목록·수정 폼 가로 스크롤 없음, JS 오류 없음. 첫 확인에서 404 후 목록을 다시 불러오면 안내 배너가 바로 지워지는 문제를 발견해, 다시 불러오기 성공 후 안내를 보여 주도록 고친 뒤 데이터를 지우고 전체를 다시 확인했다. 시험 데이터 삭제 후 restaurants 0건.
  - 남은 오류: 없음. 검색·필터는 받아 온 목록으로 화면에서 계산한다(API 필터는 L02에 있음). 추천 화면은 L07.
- [x] L07: 추천 화면(조건 선택 + 카드 뽑기 애니메이션 + 결과에서 "먹었어요").
  확인: 조건에 맞는 결과만, 없으면 안내, 애니메이션 후 결과 표시, 375px 화면 가로 스크롤 없음.
  - 변경 파일: frontend/src/components/RecommendPanel.jsx(신규, 종류·가격대 여러 개 선택, 최근 N일 제외 입력, 카드 섞기→뒤집기, 결과 카드에서 먹었어요), frontend/src/App.jsx(추천 영역 배치, 뽑힌 식당을 목록에 반영), frontend/src/constants.js(EXCLUDE_DAYS_MAX), frontend/src/App.css(칩·카드 3D 뒤집기·섞기 애니메이션, 움직임 줄이기 설정 시 애니메이션 끔)
  - 실행 명령: 백엔드 python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 --reload / 화면 cd frontend && npm run dev → http://127.0.0.1:5173
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 25개 통과 + L05 21개·L06 24개 회귀 통과, lint 경고 0, build 성공): 처음 카드 뒷면. 뽑는 중 섞기 연출·버튼 비활성·"카드 섞는 중…", 연타해도 추천 요청 1번, 결과는 카드 뒤집힘·이름·"다시 뽑기". 방문일이 다른 식당 4개로 조건마다 12~16번 뽑아 허용된 식당만 나오고 여러 식당이 나옴: 조건 없음, 한식, 한식+중식, 저렴, 한식·최근 1일 제외(오늘 간 곳 제외), 최근 7일 제외(6일 전까지 제외, 7일 전 포함). 맞는 식당 없음 → 안내·카드 뒷면. 최근 일수 31·-1·1.5·빈 값은 화면에서 거절(요청 안 함). HTML 이름·메모가 카드에 글자로 표시. 카드에서 먹었어요 → 로컬 오늘 날짜 저장·카드와 목록에 표시. 목록에서 수정하면 카드에 반영, 삭제하면 카드가 뒷면으로. API 중지 시 오류 안내·재시작 후 다시 뽑기 성공. 움직임 줄이기 설정이면 섞기·뒤집기 없이 바로 결과. 375px 가로 스크롤 없음(스크린샷 확인), JS 오류 없음. L05 회귀 시험은 화면에 오류 문구 칸이 하나 더 생겨 시험 스크립트의 선택자를 등록 폼으로 좁힌 뒤 통과(앱 동작 문제 아님). 시험 데이터 삭제 후 restaurants 0건.
  - 남은 오류: 없음. 사용자 브라우저에서 애니메이션을 직접 보는 확인은 아직 하지 않았다.
## 3장: 실행 구성
- [x] L08: 화면 빌드본(npm run build) 제공 방식과 실행 명령 정리(개발 서버 한 대, 계층별 역할 분리).
  확인: 빌드본 화면에서 등록·추천 동작, 실행 명령을 문서로 재현 가능.
  - 변경 파일: frontend/vite.config.js(빌드본 제공 preview 127.0.0.1:4173, /api → 8100 전달, 전달 주소를 API_TARGET 하나로), README.md(신규, 3티어 구성표·처음 준비·실행 명령·서버 분리 방법)
  - 구성: 프레젠테이션(화면 파일만 제공, 개발 5173·빌드본 4173) → 애플리케이션(FastAPI 8100, DB 접근 담당) → 데이터(MariaDB 3306, lunch_pick). 모두 127.0.0.1에서만 열림. Task Flow와 포트·DB 겹치지 않음.
  - 실행 명령: 터미널 1 .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 / 터미널 2 cd frontend && npm run build && npm run preview → http://127.0.0.1:4173 (개발용은 npm run dev → 5173)
  - 확인 결과(2026-10-14): README 절차대로 새 가상환경에 pip install -r requirements.txt, 새 폴더에 npm ci(package-lock.json) 성공, check_db 접속 성공, init_db는 기존 테이블 그대로. npm run lint 경고 0, npm run build 성공. README 명령 그대로(--reload 없이) API와 npm run preview 실행: 4173이 빌드 결과(dist의 index-*.js)를 제공하고 /api를 8100으로 전달. 빌드본(4173)에서 L05 21개·L06 24개·L07 25개 브라우저 확인 모두 통과(등록·목록·검색·필터·수정·삭제·먹었어요·카드 뽑기 추천). 4173·8100은 127.0.0.1에서만 수신, Task Flow(8001·localhost) 정상. 확인 후 서버 종료, 시험 데이터 삭제(restaurants 0건), dist 삭제(.gitignore 제외 대상).
  - 남은 오류: 없음. 실제 별도 서버 분리와 Nginx 등 운영 웹 서버 구성은 PLAN 범위 밖이며 README에 방법만 적었다.
## 4장: 선호도와 패스(PRD R11~R13, 2026-10-14 추가)
기존 데이터(사용자가 등록한 식당)는 지우지 않는다. 시험은 이름이 "zz시험"으로 시작하는 식당만 만들고 지운다.
- [x] L09: restaurants에 preference 열 추가(ALTER, 기존 행은 null), API에 preference 필드, 추천에 exclude_disliked·exclude_ids 조건. API-SPEC 갱신.
  확인: init_db 재실행 시 기존 행 유지, preference 등록·수정·null로 삭제, 잘못된 값 422, 별로 제외·패스 id 제외가 추천에 반영, 기존 API 계약 유지.
  - 변경 파일: backend/schemas.py(Preference, 등록·수정·응답에 preference — 수정 시 null이면 삭제), backend/models.py(preference 열·CHECK), backend/init_db.py(preference 열 없으면 ALTER TABLE ADD COLUMN), backend/main.py(응답·등록에 preference, 추천 exclude_disliked·exclude_ids 최대 100개), API-SPEC.md
  - 실행 명령: .venv 활성화 후 python -m backend.init_db → python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100
  - 확인 결과(2026-10-14, HTTP 요청 자동 확인 28개 통과 + L03 46개 회귀 통과, 임시 8101번에서 확인): 작업 전 사용자가 등록한 식당 8개를 scratchpad에 백업. init_db 1회차 preference 열 추가·2회차 그대로, SHOW CREATE TABLE로 열·CHECK 확인, 사용자 식당 8개 그대로(preference null). 등록 기본 null, LIKE·SOSO·DISLIKE 등록, 소문자·잘못된 값·숫자 422. PATCH preference만 변경·다른 필드 수정 시 유지·null로 삭제·잘못된 값 422, 다른 필드 null은 여전히 422, 방문 기록 후 유지, 목록 응답에 preference. 추천(시험 식당만 대상, 조건마다 60번): 기본은 별로 포함(기존 동작 유지), exclude_disliked=true면 별로만 제외·미지정 포함, exclude_ids 여러 개 제외, 두 조건 함께, 모두 제외 404, 없는 id 무시, 100개 허용, 문자·소수 id·잘못된 불리언·101개 422. 시험은 "zz시험" 식당과 L03 시험 식당만 만들고 삭제했으며, 시험 후 사용자 식당 8개가 시험 전과 같음을 확인.
  - 남은 오류: 없음. 예전 시험(L02·L04)은 빈 DB를 전제로 해 사용자 데이터가 있는 지금은 실행하지 않았다(사용자 데이터 보호). 화면은 L10에서 반영한다.
- [x] L10: 화면에 선호도(등록·수정·목록·카드 표시), 추천의 "별로 빼기"(기본 켬), 결과 카드의 "패스" 버튼.
  확인: 선호도 저장·표시, 별로 빼기 동작, 패스한 식당이 다시 나오지 않음, 조건 변경 시 패스 초기화, 남은 식당 없을 때 안내, 375px 가로 스크롤 없음.
  - 변경 파일(커밋 0e4ed8a): frontend/src/constants.js(선호도 이름, 입력 검증에 preference — 빈 값은 null, EXCLUDE_IDS_MAX), frontend/src/components/RestaurantForm.jsx·RestaurantEditForm.jsx(선호도 선택), RestaurantList.jsx(선호도 배지), RecommendPanel.jsx(별로 빼기 체크 기본 켬, 패스 버튼·패스 목록·패스 초기화, 조건 변경 시 패스 초기화, 카드에 선호도 배지), App.css
  - 실행 명령: API .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 / 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 25개 통과, lint 경고 0, build 성공): 등록 폼 선호도(기본 선택 안 함), LIKE 등록 → API·배지 "좋아요", 선택 안 함 → null, 수정으로 별로·선택 안 함(null). 시험 식당(양식 3곳: 미지정·좋아요·별로)으로 별로 빼기 켬 → 별로 안 나옴, 끄면 3곳 모두 나옴. 패스 → 다른 식당·"패스한 식당 1곳", 다시 뽑아도 패스한 식당 안 나옴, 모두 패스 → 없음 안내·초기화, 가격대·별로 빼기·최근 일수를 바꾸면 패스 초기화, 패스는 DB 불변. 375px 가로 스크롤 없음·카드 내용 잘림 없음, JS 오류 없음. 사용자 식당은 시험 전과 같음.
  - 기록 누락 정정(2026-10-14, L19): 처음 완료할 때 `grep -c`(경고 0개면 실패로 끝남)와 PLAN 기록 명령을 &&로 이어 기록 명령이 실행되지 않았고, 커밋 0e4ed8a에는 PLAN이 빠졌다(커밋 메시지는 "PLAN 기록"). 전체 검토에서 발견해 L10 시험 25개를 다시 실행·통과(lint 경고 0)한 뒤 이 항목을 기록했다. L13~L18의 "L10 25개 회귀 통과" 기록은 실제 실행 결과다.
## 5장: 메뉴 뽑기(PRD R14~R16, 2026-10-14 추가)
- [x] L11: 기본 메뉴 목록(종류별 10개, 60개)과 메뉴 추천 API(GET /api/menu-recommendation: 종류 여러 개, 패스한 메뉴 제외). API-SPEC 갱신.
  확인: 고른 종류의 메뉴만 나옴, 패스 제외, 남은 메뉴 없으면 404, 잘못된 값 422, 메뉴 목록 이름 중복 없음, 기존 API 영향 없음.
  - 변경 파일: backend/menus.py(신규, 종류별 10개·60개 고정 목록, id 1~60), backend/schemas.py(Menu), backend/main.py(GET /api/menu-recommendation), API-SPEC.md
  - 실행 명령: .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 (확인은 임시 8101번에서 함)
  - 확인 결과(2026-10-14, HTTP 요청 자동 확인 16개 통과): 메뉴 60개·이름 중복 없음·종류별 10개. 조건 없이 600번 → 6개 종류 모두·서로 다른 메뉴 50개 이상, 응답 id·name·category. 중식 150번 → 중식 10개만 모두 나옴(짜장면 id 11·CHINESE). 한식+분식 → 두 종류 20개만. 중식 9개 패스 → 마라샹궈만, 10개 모두 패스 → 404 No matching menu, 없는 id 무시, 100개 허용. 잘못된·소문자 category, 문자 id, 101개 422. 메뉴 추천은 식당 데이터 불변, 기존 식당 추천 API 정상. 처음 확인 때 "100개 허용" 시험이 실제 메뉴 id(0~99)를 써서 모든 메뉴가 빠져 404가 나왔고(앱은 정상), 없는 id(1000~1099)로 고친 뒤 통과.
  - 남은 오류: 없음. DB를 쓰지 않으므로 메뉴 목록은 코드 수정과 API 재시작으로만 바뀐다. 화면은 L12.
- [x] L12: 화면에 식당 뽑기/메뉴 뽑기 전환, 메뉴 카드 뽑기·패스, 결과에 같은 종류 내 식당 표시.
  확인: 식당 0개여도 메뉴 추천, 같은 종류 내 식당 표시·없으면 안내, 패스·조건 변경·모드 전환 시 초기화, 375px 가로 스크롤 없음.
  - 변경 파일: frontend/src/components/RecommendSection.jsx(신규, 식당 뽑기/메뉴 뽑기 전환), frontend/src/components/MenuPanel.jsx(신규, 종류 선택·메뉴 카드 뽑기·패스·같은 종류 내 식당), frontend/src/components/RecommendPanel.jsx(제목·section을 RecommendSection으로 옮김), frontend/src/App.jsx, frontend/src/App.css
  - 실행 명령: API .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 / 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 18개 통과, lint 경고 0, build 성공): 처음은 식당 뽑기, 메뉴 뽑기로 전환 시 메뉴 패널·"메뉴 뽑기" 버튼. 조건 없이 뽑기 → 카드 뒤집힘·메뉴 이름·종류 배지·"추천 메뉴: 이름 (종류)". 중식 12번 → 중식 메뉴만. 같은 종류 내 식당: 중식 → 시험 중식 식당, 한식(없음) → "한식 종류로 등록한 식당이 없습니다" 안내, 기타 → 사용자가 등록한 기타 식당 8곳. 패스 → 다른 메뉴·"패스한 메뉴 1개", 중식 10개를 패스하며 같은 메뉴 반복 없음, 모두 패스 → 없음 안내·초기화, 초기화 후 다시 뽑기. 종류 변경·모드 전환 시 패스·카드 초기화. 식당 뽑기 탭 기존 동작 유지. 375px 가로 스크롤 없음(스크린샷 확인), JS 오류 없음. DB 접속이 안 되는 임시 API(8101)에서도 메뉴 추천 200(식당 목록은 503) — 식당·DB 없이 메뉴 뽑기 가능. 시험은 "zz시험" 식당 1곳만 만들고 삭제, 사용자 식당 8개 그대로.
  - 남은 오류: 없음. 같은 종류 내 식당은 음식 종류 기준이며 그 메뉴를 실제로 파는지는 확인하지 않는다(PRD R16).
## 6장: 버튼 포크 애니메이션(PRD R17, 2026-10-14 추가)
- [x] L13: 버튼을 누르면 포크가 찍는 애니메이션. 선택 유지 버튼(탭·칩)은 선택된 동안 포크 유지, 한 번 누르는 버튼은 찍고 바로 사라짐.
  확인: 한 번 누르는 버튼에 포크가 나타났다 사라짐(화면에 남지 않음), 탭·칩은 선택된 것에만 포크 유지·선택 해제 시 사라짐, 비활성 버튼은 효과 없음, 움직임 줄이기 설정 존중, 기존 기능 영향 없음, 375px 가로 스크롤 없음.
  - 변경 파일: frontend/src/forkEffect.js(신규, 문서 전체 버튼 클릭 시 🍴를 버튼 위에 붙였다가 애니메이션 후 제거 — 탭·비활성 버튼·움직임 줄이기 설정은 제외), frontend/src/App.jsx(효과 설치·해제), frontend/src/App.css(찍고 사라지는 애니메이션, 선택된 탭·칩의 ::before 포크 유지)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 19개 통과 + L10 25개·L12 18개 회귀 통과, lint 경고 0, build 성공): 선택된 탭에만 포크, 메뉴 탭으로 바꾸면 0.8초 뒤에도 포크 유지·이전 탭은 사라짐, 탭·칩 클릭은 찍는 포크를 만들지 않음. 선택한 칩에만 포크 유지, 해제하면 사라짐. 뽑기 버튼 → 포크 1개(🍴, aria-hidden, 화면 고정 위치), 섞는 중(비활성) 클릭은 추가 안 됨, 1초 뒤 0개. 패스·등록 버튼에도 포크가 나타났다 사라짐, 등록 기능 정상. 5번 연타해도 포크가 남지 않음. 움직임 줄이기 설정이면 찍는 포크 없음·탭 포크는 움직임 없이 표시. 375px에서 칩 6개 모두 선택·포크가 떠 있는 동안에도 가로 스크롤 없음, JS 오류 없음. 첫 실행 때 시험 스크립트가 메뉴 패널이 그려지기 전에 칩을 눌러 멈췄고(앱 문제 아님), 남은 시험 식당 2개를 지운 뒤 기다리도록 고쳐 다시 확인했다. 시험 식당은 모두 삭제, 사용자 데이터 변화 없음.
  - 남은 오류: 없음. 시험 브라우저에는 이모지 글꼴이 없어 스크린샷에서 🍴가 네모로 보였다(사용자 브라우저에서는 이모지로 표시). 실제 브라우저에서 보이는 모양은 사용자 확인이 필요하다.
- [x] L14: 포크 애니메이션 변경(사용자 요청): 직접 그린 포크 그림, 오른쪽 위 대각선에서 날아와 버튼 오른쪽 위에 갈퀴가 박히고 떨림. 탭·칩은 꽂힌 채 유지, 한 번 누르는 버튼은 꽂힌 뒤 바로 사라짐. 버튼 크기에 맞춘 포크 크기.
  확인: 포크가 오른쪽 위에서 출발해 버튼 오른쪽 위 모서리에 멈춤(갈퀴 끝이 버튼 위), 탭·칩 유지·해제 시 사라짐, 한 번 누르는 버튼은 사라짐, 움직임 줄이기 설정 존중, 375px 가로 스크롤 없음, 기존 기능 영향 없음.
  - 변경 파일: frontend/public/fork.svg(신규, 직접 그린 포크 — 손잡이 위·갈퀴 4개 아래, 은색), frontend/src/forkEffect.js(🍴 이모지 대신 포크 그림, 버튼 높이에 맞춘 크기 28~44px, 갈퀴 끝을 버튼 오른쪽 위 모서리 안쪽에 맞춤), frontend/src/App.css(L13 효과를 바꿈: 오른쪽 위 대각선에서 회전하며 날아와 45도로 꽂히고 떨리는 fork-fly-in, 한 번 누르는 버튼은 이어서 사라짐, 탭·칩은 ::after로 꽂힌 채 유지, 탭 묶음 overflow 제거, 칩 위 여백, 화면 가로 넘침 방지)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 20개 통과 + L10 25개·L12 18개 회귀 통과, lint 경고 0, build 성공·dist에 fork.svg 포함): 애니메이션을 시간대별로 멈춰 측정 — 60ms 버튼 오른쪽 위 모서리에서 x+110·y-110(오른쪽 위 대각선), 200ms x+53·y-40(회전하며 접근), 330ms 모서리에 도착 후 떨림, 꽂힌 뒤 사라짐. 넓은 화면 스크린샷으로 날아오는 장면과 꽂힌 모습(갈퀴가 버튼 오른쪽 위 모서리, 손잡이는 오른쪽 위) 확인. 갈퀴 끝 자리가 버튼 오른쪽 위 안쪽(14px·6px 이내), 포크 크기 28~44px. 선택된 탭·칩에만 포크 유지·해제 시 사라짐, 탭·칩 클릭은 날아오는 포크를 만들지 않음, 비활성 버튼 제외, 연타해도 남지 않음, 등록 기능 정상, 움직임 줄이기 설정이면 날아오는 포크 없음·꽂힌 포크는 정지 표시. 375px에서 칩 6개 모두 선택해도 가로 스크롤 없음, 처음 스크린샷에서 칩 포크가 위쪽 설명 글자를 가려 여백을 늘린 뒤 다시 확인. JS 오류 없음. 시험 식당은 모두 삭제.
  - 남은 오류: 없음. 버튼이 화면 오른쪽 끝에 있으면 포크가 화면 밖에서 날아 들어온다(의도). 실제 브라우저에서의 느낌은 사용자 확인이 필요하다.
## 7장: 식당 테마(사용자 요청, 2026-10-14)
화면 꾸밈만 바꾸며 기능·PRD 요구사항은 바꾸지 않는다.
- [x] L15: 식당 테마로 화면 꾸밈 변경.
  확인: 기능 영향 없음(기존 시험 통과), 375px 가로 스크롤 없음, JS 오류 없음.
  - 변경 파일: frontend/src/index.css(테마 색 변수: 토마토 빨강·나무 갈색·크림 종이·겨자색), frontend/src/App.css(기존 색을 변수로 바꾸고 테마 추가: 맨 위 빨강·흰 체크 식탁보 띠, 나무 간판 제목, 메뉴판 종이 영역(이중 테두리·점선 제목·~ 장식), 체크무늬 카드 뒷면, 버튼 눌림 그림자), frontend/src/App.jsx(제목을 간판 header로 감쌈·"오늘의 식당" 부제, 식당 등록을 메뉴판 section으로 묶음), frontend/src/components/RecommendSection.jsx(메뉴판 클래스)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14): 시험 식당 3곳을 잠시 넣고 1000px·375px 스크린샷으로 간판·식탁보 띠·메뉴판 3개·체크무늬 카드 뒷면·카드 앞면·목록 확인(외부 글꼴 없이 기기 글꼴 사용). 1000px·375px 모두 가로 스크롤 없음, JS 오류 없음. L10 25개·L12 18개·L14 20개 브라우저 확인 회귀 통과, lint 경고 0, build 성공. 시험 식당 삭제 후 식당 0건.
  - 남은 오류: 없음. 제목 글꼴은 기기에 나눔명조·바탕이 있으면 그것을, 없으면 기본 명조체를 쓴다. 실제 브라우저에서의 느낌은 사용자 확인이 필요하다.
- [x] L16: 테마 변경(사용자 요청, 참고 그림의 분위기만 반영): 하늘색 배경·구름·해, 줄무늬 차양 아래 둥근 크림색 간판, 주황 땅. 맨 위 제목을 "오늘의 메뉴는~?"으로 바꾸고 개구쟁이 느낌 글씨체(주아체, OFL)를 앱에 포함.
  확인: 제목 문구·글씨체 적용, 기능 영향 없음(기존 시험 통과), 움직임 줄이기 설정 존중, 375px 가로 스크롤 없음, JS 오류 없음, 외부 글꼴 요청 없음.
  - 변경 파일: frontend/package.json·package-lock.json(@fontsource/jua 5.3.0 고정, 제목용 주아체 — SIL OFL 1.1, 앱 빌드에 포함), frontend/src/main.jsx(글씨체 불러오기), frontend/src/App.jsx(제목 "오늘의 메뉴는~?" 글자별 span·aria-label, 간판 이름표와 차양, 부제 "오늘도 맛있게!"), frontend/src/index.css(테마 색 변수 교체: 주황·하늘·크림·갈색·연두, 제목 글씨체 변수), frontend/src/App.css(L15 테마를 바꿈: 하늘 그라데이션·구름·해 배경, 아래 주황 땅·덤불, 둥근 크림 간판·물결 끝 줄무늬 차양, 흰 테두리 둥근 영역·주황 이름표 제목, 차양 줄무늬 카드 뒷면, 둥근 버튼·탭, 글자별 기울임·통통 튀는 제목)
  - 새 패키지: @fontsource/jua 5.3.0(목적: 개구쟁이 느낌 제목 글씨체를 외부 사이트 없이 앱에 포함. 글자 범위별로 나뉜 woff2 81개 중 화면에 필요한 것만 불러옴)
  - 실행 명령: 화면 cd frontend && npm install(새 패키지) && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14): 1000px·375px 스크린샷으로 하늘·구름·해·간판·차양·이름표 제목·카드 뒷면·목록·땅 확인. 제목 "오늘의 메뉴는~?"(화면 읽기용 aria-label 같음), 주아체 적용(document.fonts.check 통과, 글꼴 파일 10개 로드), 외부 주소 요청 0건. 처음 스크린샷에서 제목 빈칸이 사라지고(글자 상자 안 빈칸), 차양 아래가 안쪽으로 파여 보이고, 구름이 차양 뒤에 겹쳐 고친 뒤 다시 확인. 제목 글자 통통 튐 동작, 움직임 줄이기 설정 시 멈춤. 1000px·375px 가로 스크롤 없음, JS 오류 없음. L10 25개·L12 18개·L14 20개 회귀 통과, lint 경고 0, build 성공. 시험 식당 삭제 후 0건.
  - 남은 오류: 없음. 카드 뒷면 문구와 브라우저 탭 제목은 "오늘 뭐 먹지?" 그대로다(요청 범위는 맨 위 제목). 참고 그림은 분위기만 참고했고 그림·제목을 옮기지 않았다.
- [x] L17: 카드 뒷면을 물음표만 두고 기대감 있게 꾸밈(두근거리는 ? 접시·빛, 반짝이, 떠오르는 작은 물음표, 빛줄기), 식당·메뉴 카드 뒷면 공통 부품. 브라우저 탭 제목 "오늘의 메뉴는~?".
  확인: 뒷면에 글자 문구 없음·물음표 표시, 꾸밈 애니메이션 동작·움직임 줄이기 시 멈춤, 카드 뽑기·뒤집기 동작 유지, 탭 제목, 375px 가로 스크롤 없음, JS 오류 없음.
  - 변경 파일: frontend/src/components/CardBack.jsx(신규, 공통 카드 뒷면), frontend/src/components/RecommendPanel.jsx·MenuPanel.jsx(뒷면을 CardBack으로, "오늘 뭐 먹지?" 문구 삭제), frontend/index.html(탭 제목 "오늘의 메뉴는~?"), frontend/src/App.css(뒷면 문구 스타일 삭제, ? 접시 갸우뚱·두근 커짐·빛 퍼짐, 노란·갈색 네 갈래 반짝이 4개, 흰 테두리 갈색 작은 물음표 3개 떠오름, 빛줄기 지나감, 움직임 줄이기 시 정지)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 9개 통과 + L10 25개·L12 18개·L14 20개·제목 3개 회귀 통과, lint 경고 0, build 성공): 탭 제목 "오늘의 메뉴는~?", 뒷면 글자는 물음표뿐(큰 ? 1·작은 ? 3), 반짝이 4·빛줄기, 애니메이션 4종(mark-wonder·sparkle-twinkle·mini-float·card-shine) 동작, 메뉴 뽑기 카드도 같은 뒷면, 뽑기 후 뒤집혀 결과 표시·뒷면 숨김. 시간대별(0.3·0.9·1.5·2.7초) 스크린샷 확인 — 처음엔 흰 반짝이·크림색 작은 물음표가 흰 줄무늬에서 안 보여 갈색 별·흰 테두리 갈색 물음표로 바꾼 뒤 다시 확인. 움직임 줄이기 시 애니메이션 0개·반짝이 정지 표시. 375px 가로 스크롤 없음, JS 오류 없음. 식당 데이터 변화 없음(0건).
  - 남은 오류: 없음.
- [x] L18: 뽑기 버튼(식당·메뉴)을 화면 폭과 관계없이 항상 오른쪽 끝에 정렬(사용자 요청).
  확인: 여러 화면 폭에서 두 뽑기 버튼 모두 줄의 오른쪽 끝, 가로 스크롤 없음, 기존 기능 영향 없음.
  - 변경 파일: frontend/src/App.css(.recommend-row .draw-button에 margin-left: auto)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium): 고치기 전 320px 메뉴 뽑기, 480px·540px 식당 뽑기에서 버튼이 다음 줄 왼쪽으로 내려감을 재현. 고친 뒤 폭 12가지(320~1200px) × 식당·메뉴 24곳 모두 버튼 오른쪽 끝이 줄 오른쪽 끝과 일치, 가로 스크롤 없음. L10 25개·L12 18개·L17 9개 회귀 통과, lint 경고 0.
  - 남은 오류: 없음.
## 8장: 전체 검토 후 수정(2026-10-14)
전체 검토(백엔드·화면·문서 검토자 3명 + 직접 재현) 결과 중 먼저 고칠 것을 작업으로 나눈다.
- [x] L19: 기록·문서 정리 — L10 기록 누락 정정, L18 실행 명령, PLAN 포트에 4173, README(앱 화면 이름·기능 설명·.env 위치·init_db 설명), PRD에 화면 이름.
  확인: 문서 내용이 실제 파일·코드와 맞음.
  - 변경 파일: PLAN.md(L10 기록·누락 경위, L18 실행 명령, 포트에 4173, 8장 L19~L21), README.md(제목에 화면 이름, 선호도·별로 빼기·패스·메뉴 뽑기 설명, .env는 프로젝트 루트, init_db는 없는 테이블·열만 추가), PRD.md(화면 이름 "오늘의 메뉴는~?" 한 줄)
  - 실행 명령: 없음(문서 작업). L10은 다시 확인: 화면 cd frontend && npm run dev 후 L10 브라우저 시험
  - 확인 결과(2026-10-14): L10 시험 25개 다시 실행·통과, lint 경고 0. README의 .env 위치(backend/database.py가 PROJECT_ROOT/.env를 읽음), init_db 열 추가(ALTER TABLE ADD COLUMN), 메뉴 60개를 코드에서 확인. 커밋에 PLAN.md가 들어갔는지 git show --stat으로 확인.
  - 남은 오류: 없음. AGENTS.md·API-SPEC.md·PLAN.md 제목의 "오늘 뭐 먹지?"는 프로젝트 이름이라 그대로 둔다(PRD에 명시).
- [x] L20: 화면 버그 — 카드를 섞는 동안 숨겨진 결과 카드의 버튼이 눌리는 문제, 다른 식당 요청 중 삭제가 안내 없이 무시되는 문제, L18 이후 "별로 빼기" 체크박스 위치가 화면 폭마다 달라지는 문제.
  확인: 섞는 중 숨겨진 버튼 사용 불가·방문 기록 안 됨, 요청 중에는 다른 식당 버튼 비활성·확인 창 안 뜸, 여러 폭에서 조건은 왼쪽부터·뽑기 버튼은 오른쪽 끝, 기존 시험 통과.
  - 변경 파일: frontend/src/components/RecommendPanel.jsx(결과 앞면에 inert — 결과가 보일 때만 사용 가능, 섞는 중 먹었어요 막음), frontend/src/components/MenuPanel.jsx(결과 앞면에 inert), frontend/src/components/RestaurantList.jsx(어느 식당이든 요청 중이면 모든 항목 버튼 비활성, 요청 중 삭제는 확인 창 전에 막음), frontend/src/App.css(.recommend-row를 flex-start로, 뽑기 버튼 오른쪽 정렬 규칙을 같은 자리로 옮기고 L18 끝 규칙 삭제)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 15개 통과 + L10 25개·L12 18개·L14 20개·L17 9개·L18 24곳 회귀 통과, lint 경고 0, build 성공): 결과가 보일 때 앞면 사용 가능, 패스 후 섞는 중에는 앞면 inert·먹었어요에 초점 안 감·눌러도 방문 기록 요청 0건, 섞기 끝나면 다시 사용 가능, 패스한 식당 방문일 그대로. 메뉴 카드도 뒷면·섞는 중 앞면 inert. 먹었어요 요청을 1.5초 늦춘 상태에서 다른 식당의 먹었어요·수정·삭제 버튼 비활성, 삭제를 눌러도 확인 창 0번, 요청이 끝나면 다시 사용 가능, 그다음 삭제는 확인 창 1번·실제 삭제. 폭 9가지(320~1000px)에서 "별로 빼기"는 같은 줄이면 "최근 □일" 바로 뒤(10px), 뽑기 버튼은 오른쪽 끝, 가로 스크롤 없음. 처음 실행 때 시험 스크립트 오류 2번(기다리는 함수 안 도우미 이름, 같은 줄 판정을 윗변으로 함 — 앱 문제 아님)을 고치고 남은 시험 식당 3개를 지운 뒤 다시 확인. 사용자 식당 변화 없음(0건).
  - 남은 오류: 없음.
- [x] L21: 백엔드 오류 처리 — 아주 이른 날짜(today=0001-01-01 등)의 500, DB 오류가 모두 503으로 뭉뚱그려지고 로그가 없는 문제.
  확인: 1000년 이전 날짜 422(추천·방문 기록), 연결 오류만 503·나머지 DB 오류는 500, 서버 로그에 오류 기록(비밀번호 없음), 기존 API 시험 통과.
  - 변경 파일: backend/schemas.py(validate_date: 1000-01-01 이전 날짜 거절 — 추천 today·방문 기록 visited_on 공통), backend/main.py(OperationalError 처리기를 DBAPIError 처리기로: 서버 로그에 드라이버 오류 번호·메시지만 기록, 연결 오류 번호 1044·1045·1049·2002·2003·2006·2013과 끊긴 연결은 503, 그 밖의 DB 오류는 500 Internal server error), API-SPEC.md(500 추가, 503 설명, 날짜 범위)
  - 실행 명령: .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 (확인은 임시 8101·8102·8103에서 하고, 끝난 뒤 8100을 새 코드로 다시 시작)
  - 확인 결과(2026-10-14): 처리기 단위 확인 8개 통과(2003·1045·2013·끊긴 InterfaceError → 503, 1054·1205·4025·1062 → 500, 응답 본문에 내부 내용 없음, 오류마다 로그 1줄). 추천 today 0001-01-01·0999-12-31 → 422(전에는 0001-01-01이 500), 1000-01-01·9999-12-31 → 정상 처리, 방문 기록 0001·0999년 422·1000·9999년·오늘 200. 잘못된 DB 포트 API(8102) 목록 503·메뉴 뽑기 200, 가짜 비밀번호 API(8103) 503, 두 서버 로그에 "DB 오류 … OperationalError (2003/1045, …)" 기록, 로그에 진짜·가짜 비밀번호 0건·SQL 문장 0건. 기존 API 시험 L09 27개·L03 46개 통과, L11은 15/16 — 실패 1개(식당 추천 기타)는 사용자가 지운 기타 식당 8곳을 전제한 시험이라 식당 0개에서 404가 맞고, 기타 시험 식당 1곳을 넣어 200을 확인한 뒤 삭제. 시험 식당 모두 삭제(0건), 8100 새 코드로 다시 시작·화면(4173) 연결 정상.
  - 남은 오류: 없음. 검토의 작은 항목(동시 삭제 경합 시 404 대신 500/204, 일부 422 본문 모양, 깨진 유니코드 500, exclude_disliked의 yes/on 허용)과 화면 작은 항목은 이번 범위에 넣지 않았다.
- [x] L22: 카드를 뽑으면 결과 이름(식당·메뉴)이 "띠용" 하고 크게 튀어나왔다가 제자리로 돌아오는 강조(사용자 요청). "띠용!" 글자가 톡 나왔다 사라지고, 이름에 형광펜 강조가 남음. 뽑을 때마다 다시 재생.
  확인: 결과마다 튀어나오는 애니메이션 재생(같은 결과 연속도), 끝나면 원래 크기·"띠용!" 사라짐, 움직임 줄이기 시 움직임 없이 강조만, 375px 가로 스크롤 없음, 기존 기능 영향 없음.
  - 변경 파일: frontend/src/components/RevealName.jsx(신규, 결과 이름 + "띠용!" 장식), frontend/src/components/RecommendPanel.jsx·MenuPanel.jsx(결과 이름을 RevealName으로, 결과마다 늘어나는 revealCount를 key로 써서 애니메이션 다시 재생), frontend/src/App.css(name-boing: 작게 시작 → 크게 튀어나옴 → 줄었다 늘었다 → 원래 크기, boing-burst: "띠용!"이 톡 나왔다 사라짐, 이름 아래 노란 형광펜, 움직임 줄이기 시 정지)
  - 실행 명령: 화면 cd frontend && npm run dev(5173) 또는 npm run build && npm run preview(4173)
  - 확인 결과(2026-10-14, Headless Chromium 자동 확인 10개 통과 + L10 25개·L12 18개·L17 9개·L20 15개 회귀 통과, lint 경고 0, build 성공): 메뉴·식당 결과 모두 이름 애니메이션·"띠용!"(aria-hidden). 애니메이션을 멈춰 잰 이름 크기 0.4초 ×0.88 → 0.64초 ×1.31(가장 큼) → 0.83초 ×0.9 → 1.3초 이후 ×1, "띠용!"은 0.64~0.83초에 보이고 2초에 사라짐. 패스해 다시 뽑으면 새로 재생, 같은 식당이 연속으로 나와도 다시 재생. 움직임 줄이기 시 애니메이션 없음·"띠용!" 숨김·형광펜 남음. 375px에서 50자 이름이 가장 클 때도 가로 스크롤 없음, JS 오류 없음. 처음 스크린샷에서 "띠용!"이 위의 "오늘의 메뉴!" 글자를 가려 이름 옆으로 옮긴 뒤 다시 확인. 시험 식당 삭제, 식당 0건.
  - 남은 오류: 없음.
## 9장: 회원가입·로그인(PRD R18~R21, 2026-10-14 추가)
Task Flow(같은 컴퓨터의 다른 프로젝트) 6장과 같은 방식을 쓰되, 쿠키 이름은 lunch_pick_session으로 다르게 한다. 기존 데이터·테이블은 지우지 않는다. 시험은 "zz"로 시작하는 시험 사용자·식당만 만들고 지운다.
- [x] L23: PRD(R18~R21)·API-SPEC(인증 API, User, 세션 쿠키, 401·409, 식당 API 로그인 필수) 작성.
  확인: R18~R21 규칙(아이디·비밀번호 길이, 중복 409, 같은 401, 다른 사용자 식당 404, 메뉴 추천은 로그인 무관)이 명세에 모두 있음.
  - 변경 파일: PRD.md(사용자와 범위, R18~R21, 데이터에 user_id·사용자·세션, 제외 기능에서 회원가입·로그인 삭제·비밀번호 찾기 등 추가, 완료 기준), API-SPEC.md(엔드포인트 표, 공통 인증 규칙, user_id, 401·409, auth 422 input 미포함, User, 세션 쿠키 lunch_pick_session, auth 4개 API, 메뉴 추천 로그인 무관)
  - 실행 명령: 없음(문서 작업). grep으로 명세 항목 확인.
  - 확인 결과(2026-10-14): 아이디 ^[a-z0-9]{4,20}$·비밀번호 8~64자·409·같은 401 메시지·다른 사용자 식당 404·Not authenticated·HttpOnly 쿠키·auth 422 input 미포함·메뉴 추천 로그인 무관이 명세에 모두 있음. 코드는 바꾸지 않았다.
  - 남은 오류: 없음. 쿠키 Secure는 HTTP 학습용이라 붙이지 않는다.
- [x] L24: users·sessions 테이블, restaurants.user_id(NULL 허용) 열 추가(init_db).
  확인: init_db 재실행 시 기존 행 유지, DB 제약(아이디 규칙·중복·외래 키) 확인.
  - 변경 파일: backend/models.py(UserRow·SessionRow, RestaurantRow.user_id NULL 허용·외래 키), backend/init_db.py(users·sessions 생성, restaurants.user_id 없으면 ALTER TABLE ADD COLUMN·인덱스·외래 키, preference 추가와 같은 방식으로 정리)
  - 실행 명령: .venv 활성화 후 python -m backend.init_db
  - 확인 결과(2026-10-14): 실행 전 식당 0건. 1회차 users·sessions 생성·restaurants.user_id 추가, 2회차 모두 "그대로 두었습니다". SHOW CREATE TABLE로 utf8mb4_bin 아이디·UNIQUE·CHECK, 세션 UNIQUE·외래 키, restaurants.user_id 인덱스·외래 키 확인. 트랜잭션 안에서 확인 후 ROLLBACK(16개 통과): 아이디 4·20자·소문자+숫자 허용, 중복·대문자·3자·21자·공백·한글·밑줄 거절, 세션 정상·중복·없는 사용자 거절, 식당 주인 있음·NULL 허용·없는 사용자 거절. 확인 후 users·sessions 0건(AUTO_INCREMENT 1), 식당 0건.
  - 남은 오류: 없음. API는 아직 user_id를 쓰지 않는다(L26).
- [x] L25: 회원가입·로그인·로그아웃·현재 사용자 API(비밀번호 scrypt 해시, 세션 쿠키).
  확인: 정상·위반·중복, 같은 401, 쿠키 속성, 로그아웃 후 401, API 재시작 후 로그인 유지, 응답·로그에 비밀번호 없음.
  - 변경 파일: backend/security.py(신규, Task Flow의 같은 모듈: scrypt 해시·검증, 없는 아이디용 더미 해시, 세션 값 생성·SHA-256), backend/schemas.py(SignupRequest·LoginRequest·User), backend/main.py(POST /api/auth/signup·login·logout, GET /api/auth/me, get_current_user 의존성 — L26에서 식당 API에 사용, 인증 API 422에서 보낸 값 제거, 쿠키 lunch_pick_session)
  - 실행 명령: .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 (확인은 임시 8101번)
  - 확인 결과(2026-10-14, HTTP 요청 자동 확인 79개 통과 — Task Flow T17·T18 시험을 이 앱 주소·DB·쿠키 이름으로 바꿔 실행): 회원가입 32개(정상 201·응답에 비밀번호·쿠키 없음, 4·20자·8·64자·앞뒤 공백·한글 비밀번호 허용, 중복 409, 규칙 위반·누락·숫자·null·정의 안 된 필드·배열·깨진 JSON 422, 422 응답에 보낸 비밀번호 없음, DB에 원문 없음·salt 모두 다름·검증 함수 확인). 로그인·로그아웃 47개(로그인 200·쿠키 lunch_pick_session HttpOnly·SameSite=Lax·Path=/api·Max-Age=604800·Secure 없음·DB에는 세션 해시만·7일, me 200/401, 틀린 아이디·비밀번호·규칙 위반 모두 같은 401·쿠키 없음, 필드 오류 422, 응답 시간 비슷, 다른 곳 로그인해도 기존 세션 유지·같은 쿠키 재로그인 시 이전 세션 401, 로그아웃 204·쿠키 만료·DB 세션 삭제·같은 쿠키 401, 만료 세션 401, 임시 API 재시작(PID 변경) 후 로그인 유지). 서버 로그에 비밀번호·세션 값 0건. 시험 사용자·세션 삭제 후 users·sessions 0건.
  - 남은 오류: 없음. 식당 API는 아직 로그인 없이 동작한다(L26).
- [ ] L26: 식당 API(목록·등록·수정·삭제·방문·추천) 로그인 필수·사용자별 분리.
  확인: 비로그인 401, 두 사용자가 서로의 식당을 못 보고 못 바꿈(404), 추천은 내 식당 안에서만, 메뉴 추천은 로그인 없이 동작, 기존 API 시험 통과.
- [ ] L27: 화면에 로그인·회원가입·로그아웃, 로그인 전에는 로그인 화면.
  확인: 비로그인 시 로그인 화면, 가입·로그인·로그아웃, 내 식당만 표시, 세션 만료 시 로그인 화면, 기존 화면 기능 회귀, 375px 가로 스크롤 없음.
- [ ] L28: README 실행·준비 설명 갱신, 빌드본(4173)에서 전체 확인.
  확인: README 절차와 실제가 맞음, 빌드본에서 가입·로그인·식당·추천·메뉴 뽑기 동작.
- 중단(2026-10-14, 사용자 요청): L26은 코드 수정 중 멈췄고 수정은 되돌렸다(git restore). L26~L28은 미완료로 남긴다. L25까지의 회원가입·로그인 API는 코드에 있지만 식당 API는 아직 로그인 없이 동작한다.
## 추가 작업
- [x] ngrok 공유: 빌드본(4173)이 ngrok 주소를 막지 않게 preview.allowedHosts에 ngrok 도메인 추가.
  확인: ngrok 주소(Host)로 요청 시 200, 다른 낯선 주소는 계속 403, 로컬 주소 200.
  - 변경 파일: frontend/vite.config.js(preview.allowedHosts: .ngrok-free.app·.ngrok-free.dev)
  - 실행 명령: cd frontend && npm run build && npm run preview → (사용자) ngrok http 4173
  - 확인 결과(2026-10-14): 고치기 전 ngrok 주소 Host로 요청 시 403 "Blocked request". 고친 뒤 빌드·preview 다시 시작: Host *.ngrok-free.app·*.ngrok-free.dev 200, 낯선 주소(evil.example.com) 403 유지, 127.0.0.1:4173 200, ngrok Host로 /api/health 200. 실제 ngrok 터널 연결은 사용자가 실행한다.
  - 남은 오류: 식당 API에 아직 로그인이 없어(L26 미완료) 주소를 아는 사람은 식당을 보고 바꿀 수 있다.
## 실행 기준
작업마다 실제 존재하는 파일을 확인한 뒤 실행 명령을 기록한다.
## 기록
각 작업에 변경 파일, 실행 명령, 실제 확인 결과, 남은 오류를 기록한다.
정상 동작을 확인한 작업 단위로 Git 커밋한다.
