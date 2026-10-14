# 오늘 뭐 먹지?

자주 가는 식당과 가 보고 싶은 식당을 저장하고, 조건에 맞는 식당을 카드 뽑기로 무작위 추천받는 개인용 웹앱입니다.
요구사항은 [PRD.md](PRD.md), API는 [API-SPEC.md](API-SPEC.md), 작업 기록은 [PLAN.md](PLAN.md)에 있습니다.

## 구성(3티어, 개발 서버 한 대)

| 계층 | 기술 | 폴더 | 주소 | 역할 |
|---|---|---|---|---|
| 프레젠테이션 | React(Vite) | `frontend/` | 개발 `127.0.0.1:5173`, 빌드본 `127.0.0.1:4173` | 화면 파일 제공, `/api`는 App으로 전달 |
| 애플리케이션 | FastAPI | `backend/` | `127.0.0.1:8100` | 요청 처리, 추천 로직, DB 접근 |
| 데이터 | MariaDB | (DB 서버) | `127.0.0.1:3306`, DB `lunch_pick` | 식당 데이터 저장 |

- 화면은 `/api`만 호출합니다. DB 접속 정보는 백엔드의 `.env`에만 있고 화면 코드에는 없습니다.
- 모든 서버는 `127.0.0.1`에서만 열려 다른 컴퓨터에서는 접속할 수 없습니다.
- 같은 컴퓨터의 Task Flow(80·8000·8001번, DB `task_flow`)와 포트·DB가 겹치지 않습니다.

## 처음 한 번 준비

1. MariaDB에 전용 DB와 계정을 만듭니다(관리자 권한, 비밀번호는 직접 정함).

   ```sql
   CREATE DATABASE lunch_pick CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'lunch_pick_app'@'localhost' IDENTIFIED BY '비밀번호';
   GRANT ALL PRIVILEGES ON lunch_pick.* TO 'lunch_pick_app'@'localhost';
   ```

2. `.env`를 만들고 비밀번호를 적습니다(Git에 올라가지 않음).

   ```bash
   cp .env.example .env
   chmod 600 .env
   ```

3. 백엔드 가상환경과 패키지, 테이블을 준비합니다.

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python -m backend.check_db   # 접속 확인
   .venv/bin/python -m backend.init_db    # 테이블 생성(있으면 그대로 둠)
   ```

4. 화면 패키지를 설치합니다(npm 필요: `sudo apt install -y npm`).

   ```bash
   cd frontend && npm install
   ```

## 실행

터미널을 두 개 씁니다. 끌 때는 각 터미널에서 Ctrl+C를 누릅니다.

**터미널 1 — 애플리케이션 계층(API)**

```bash
cd ~/vibe-lab/lunch-pick
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100
```

**터미널 2 — 프레젠테이션 계층(화면)**: 둘 중 하나를 고릅니다.

```bash
cd ~/vibe-lab/lunch-pick/frontend
npm run dev                         # 개발용: http://127.0.0.1:5173 (코드 수정이 바로 반영)
npm run build && npm run preview    # 빌드본: http://127.0.0.1:4173 (dist/의 결과만 제공)
```

API 문서는 API 실행 중 http://127.0.0.1:8100/docs 에서 볼 수 있습니다.

## 나중에 서버를 나눌 때

- 데이터 계층: DB를 다른 서버로 옮기면 백엔드 `.env`의 `DB_HOST`·`DB_PORT`만 바꿉니다.
- 애플리케이션 계층: 다른 서버에서 같은 명령으로 실행하고, 화면 쪽 `/api` 전달 주소(`frontend/vite.config.js`의 `API_TARGET`, 또는 웹 서버 설정)를 그 서버로 바꿉니다.
- 프레젠테이션 계층: `npm run build`로 만든 `frontend/dist/`를 웹 서버(예: Nginx)가 제공하고 `/api`를 App 서버로 전달하게 합니다.
