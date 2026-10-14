# 오늘 뭐 먹지? API 명세

PRD의 요구사항(R01~R21)을 API로 옮긴 계약이다. 구현 순서는 PLAN을 따른다.

| 엔드포인트 | 구현 작업 |
|---|---|
| `GET /api/health` | L01 |
| `GET /api/restaurants`, `POST /api/restaurants` | L02 |
| `PATCH /api/restaurants/{id}`, `DELETE /api/restaurants/{id}`, `POST /api/restaurants/{id}/visit` | L03 |
| `GET /api/recommendation` | L04 |
| 선호도(`preference`), 추천의 `exclude_disliked`·`exclude_ids` | L09 |
| `GET /api/menu-recommendation` | L11 |
| `POST /api/auth/signup`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` | L25 |
| 식당 API의 로그인 필수·사용자별 분리(`401`) | L26 |

## 공통

- 기본 주소(개발): `http://127.0.0.1:8100`. 화면 개발 서버(5173)는 `/api` 요청을 이 주소로 전달한다(L05).
- 모든 경로는 `/api`로 시작한다. 요청·응답 본문은 JSON(UTF-8)이다.
- 인증(L25·L26): `/api/health`, `/api/auth/signup`·`login`·`logout`, `/api/menu-recommendation`을 뺀 모든 API는 로그인이 필요하다. 로그인하지 않았으면 `401` `{"detail": "Not authenticated"}`이며, 입력 검증보다 로그인 확인을 먼저 한다(본문이 틀려도 `401`).
- 식당은 로그인한 사용자 본인 것만 조회·수정·삭제·방문 기록·추천한다. 다른 사용자의 식당 `id`는 없는 식당과 같은 `404`다.
- 입력값 검증은 서버에서도 한다. 화면 검증만 믿지 않는다.
- 데이터는 MariaDB에 저장한다. API를 재시작해도 유지된다.

## 데이터: Restaurant

| 필드 | 타입 | 규칙 | 기본값 |
|---|---|---|---|
| `id` | integer | 서버가 발급하는 고유 번호. 수정·삭제·방문 기록은 이 값으로만 한다. | 서버 발급 |
| `name` | string | 앞뒤 공백을 제거한 뒤 1~50자 | 필수 |
| `category` | string | `KOREAN`, `CHINESE`, `JAPANESE`, `WESTERN`, `SNACK`, `ETC` 중 하나 | `ETC` |
| `price_range` | string | `LOW`, `MID`, `HIGH` 중 하나 | `MID` |
| `memo` | string | 0~500자 | `""` |
| `preference` | string \| null | 선호도. `LIKE`(좋아요), `SOSO`(그저 그래요), `DISLIKE`(별로) 중 하나, 미지정은 `null` | `null` |
| `last_visited_on` | string \| null | 마지막 방문일 `YYYY-MM-DD`. 방문 기록 API로만 바꾼다. | `null` |
| `created_at` | string | 서버가 기록하는 등록 시각(ISO 8601, UTC) | 서버 기록 |

```json
{
  "id": 1,
  "name": "김밥천국 역삼점",
  "category": "SNACK",
  "price_range": "LOW",
  "memo": "라볶이 맛있음",
  "preference": "LIKE",
  "last_visited_on": "2026-10-10",
  "created_at": "2026-10-14T06:30:00Z"
}
```

- `id`, `created_at`, `last_visited_on`과 정의되지 않은 필드를 등록·수정 요청으로 보내면 422로 거절한다.
- 식당의 주인(`user_id`)은 서버가 로그인한 사용자로 정한다. 응답에는 넣지 않고, 요청으로 보내면 정의되지 않은 필드로 보고 422다.

## 오류 응답

| 상태 코드 | 상황 |
|---|---|
| `401 Unauthorized` | 로그인하지 않았거나 세션이 만료·로그아웃됨(`{"detail": "Not authenticated"}`), 로그인 실패(`{"detail": "Invalid username or password"}`) |
| `404 Not Found` | 해당 `id`의 식당이 없음(`{"detail": "Restaurant not found"}`), 추천 조건에 맞는 식당이 없음(`{"detail": "No matching restaurant"}`), 조건에 맞는 메뉴가 없음(`{"detail": "No matching menu"}`) |
| `409 Conflict` | 회원가입 시 이미 있는 아이디(`{"detail": "Username already exists"}`) |
| `422 Unprocessable Entity` | 입력 규칙 위반(빈 이름, 51자 이름, 501자 메모, 잘못된 종류·가격대·날짜, 정의되지 않은 필드 등). `detail`은 위반 항목 목록(FastAPI 기본 형식) |
| `500 Internal Server Error` | 연결 외의 DB 오류(예: 테이블 열 없음, 잠금 시간 초과). `{"detail": "Internal server error"}`. 원인은 서버 로그에만 남긴다(L21). |
| `503 Service Unavailable` | DB에 연결할 수 없음(서버 꺼짐·연결 끊김·접속 정보 오류). `{"detail": "Database unavailable"}`, 접속 정보 등 내부 오류는 보여 주지 않고 원인은 서버 로그에 남긴다. |

`/api/auth/` API의 422 항목에는 보낸 값(`input`)을 넣지 않는다(비밀번호가 응답에 다시 나오지 않게).

## 데이터: User

| 필드 | 타입 | 규칙 |
|---|---|---|
| `id` | integer | 서버가 발급하는 고유 번호 |
| `username` | string | 영문 소문자·숫자 4~20자(`^[a-z0-9]{4,20}$`). 앞뒤 공백 제거·소문자 변환을 하지 않는다. 중복 불가. |
| `created_at` | string | 가입 시각(ISO 8601, UTC) |

- 비밀번호(`password`)는 요청으로만 받는다. 8~64자, 문자 종류 제한 없음, 앞뒤 공백도 비밀번호로 본다. DB에는 사용자별 salt를 쓴 scrypt 해시만 저장하고 응답·로그에 넣지 않는다.

## 인증(세션 쿠키)

- 로그인에 성공하면 쿠키 `lunch_pick_session`을 보낸다. 같은 컴퓨터의 Task Flow(쿠키 `task_flow_session`)와 섞이지 않게 이름을 다르게 한다.
  - 속성: `HttpOnly`, `SameSite=Lax`, `Path=/api`, `Max-Age=604800`(7일). 개발·학습용 HTTP 주소에서 쓰므로 `Secure`는 붙이지 않는다.
- 세션 값은 무작위 값이며 DB에는 해시·사용자·만료 시각만 저장한다. API를 재시작해도 로그인이 유지되고, 7일이 지나거나 로그아웃하면 그 세션은 `401`이다.

## 엔드포인트

### `POST /api/auth/signup`

회원가입. 가입만 하고 로그인은 하지 않는다. 본문 `{"username": "...", "password": "..."}`.

- `201 Created`: User. 규칙 위반·필드 누락·정의되지 않은 필드 `422`, 이미 있는 아이디 `409`.

### `POST /api/auth/login`

로그인. 본문은 회원가입과 같다.

- `200 OK`: User와 `Set-Cookie: lunch_pick_session=...`.
- 없는 아이디·틀린 비밀번호·규칙에 맞지 않는 값은 모두 같은 `401` `{"detail": "Invalid username or password"}`. 필드 누락·문자열이 아닌 값·정의되지 않은 필드는 `422`.
- 이미 로그인한 쿠키가 있으면 그 세션은 지우고 새로 만든다.

### `POST /api/auth/logout`

로그아웃. 현재 쿠키의 세션을 지우고 쿠키를 만료시킨다. 항상 `204 No Content`.

### `GET /api/auth/me`

현재 로그인한 사용자. `200 OK`: User, 로그인하지 않았으면 `401`.


### `GET /api/health`

- 응답 `200 OK`: `{"status": "ok"}`

### `GET /api/restaurants`

식당 목록. 등록 순서(오래된 것부터)로 돌려준다.

쿼리 파라미터(모두 선택, 함께 주면 AND 조건):

| 이름 | 설명 |
|---|---|
| `q` | 이름 검색어. 앞뒤 공백 제거 후 대소문자 구분 없이 포함 여부로 찾는다. `%`, `_`는 글자로 찾는다. 빈 값은 조건 없음. |
| `category` | 음식 종류 하나 |
| `price_range` | 가격대 하나 |

- 응답 `200 OK`: Restaurant 배열. 없으면 `[]`.
- 잘못된 `category`·`price_range`는 `422`.

### `POST /api/restaurants`

식당 등록. `name`만 필수다.

```json
{ "name": "김밥천국 역삼점", "category": "SNACK", "price_range": "LOW", "memo": "라볶이 맛있음" }
```

- 응답 `201 Created`: 생성된 Restaurant(`last_visited_on`은 `null`).
- 규칙 위반은 `422`.

### `PATCH /api/restaurants/{id}`

식당 정보 일부 수정. 보낸 필드만 바꾸고 보내지 않은 필드는 그대로 둔다.

- 바꿀 수 있는 필드: `name`, `category`, `price_range`, `memo`, `preference`. `preference`에 `null`을 보내면 선호도를 지운다. 나머지 필드에는 `null`을 보낼 수 없다(422).
- 빈 본문 `{}`은 아무것도 바꾸지 않고 현재 Restaurant를 돌려준다.
- 응답 `200 OK`: 수정된 Restaurant. 없는 `id`는 `404`, 규칙 위반은 `422`.

### `DELETE /api/restaurants/{id}`

식당 삭제. 삭제 전 확인은 화면이 한다.

- 응답 `204 No Content`. 없는 `id`는 `404`.

### `POST /api/restaurants/{id}/visit`

방문 기록("먹었어요"). 날짜는 사용자 PC의 로컬 날짜를 화면이 보낸다.

```json
{ "visited_on": "2026-10-14" }
```

- `visited_on`은 필수이며 실제 존재하는 `YYYY-MM-DD` 날짜다. 1000-01-01~9999-12-31만 받는다(L21).
- 보낸 날짜를 `last_visited_on`으로 저장한다.
- 응답 `200 OK`: 수정된 Restaurant. 없는 `id`는 `404`, 규칙 위반은 `422`.

### `GET /api/recommendation`

조건에 맞는 식당 하나를 무작위로 추천한다.

쿼리 파라미터:

| 이름 | 설명 |
|---|---|
| `category` | 음식 종류. 여러 번 줄 수 있다(`?category=KOREAN&category=SNACK`). 없으면 모든 종류. |
| `price_range` | 가격대. 여러 번 줄 수 있다. 없으면 모든 가격대. |
| `exclude_days` | 0~30. 최근 N일 안에 방문한 식당을 뺀다. 0이면 빼지 않는다. 기본값 0. |
| `today` | 사용자 PC의 로컬 날짜 `YYYY-MM-DD`(1000-01-01~9999-12-31). `exclude_days`가 1 이상이면 필수. |
| `exclude_disliked` | `true`면 선호도가 `DISLIKE`인 식당을 뺀다. 선호도 미지정은 빼지 않는다. 기본값 `false`. |
| `exclude_ids` | 뺄 식당 id(패스한 식당). 여러 번 줄 수 있다(`?exclude_ids=3&exclude_ids=5`), 최대 100개. 없는 id는 무시한다. |

- 최근 N일 안 방문: `last_visited_on`이 `today - (N - 1)`일부터 `today`까지인 식당. 예: N=1이면 오늘 방문한 곳, N=7이면 오늘 포함 7일 안에 방문한 곳을 뺀다. 방문 기록이 없는 식당은 빼지 않는다.
- 응답 `200 OK`: Restaurant 하나.
- 조건에 맞는 식당이 없으면 `404` `{"detail": "No matching restaurant"}`.
- 잘못된 값(종류·가격대·범위 밖 `exclude_days`·잘못된 날짜·`today` 누락·정수가 아닌 `exclude_ids`·101개 이상 `exclude_ids`·불리언이 아닌 `exclude_disliked`)은 `422`.

### `GET /api/menu-recommendation`

기본 메뉴 목록(음식 종류별 10개, 총 60개)에서 메뉴 하나를 무작위로 추천한다. 식당 데이터와 DB는 쓰지 않는다.
로그인 없이도 쓸 수 있다(개인 데이터가 없음).

쿼리 파라미터:

| 이름 | 설명 |
|---|---|
| `category` | 음식 종류. 여러 번 줄 수 있다. 없으면 모든 종류. |
| `exclude_ids` | 뺄 메뉴 id(패스한 메뉴). 여러 번 줄 수 있다, 최대 100개. 없는 id는 무시한다. |

- 응답 `200 OK`: Menu `{"id": 11, "name": "짜장면", "category": "CHINESE"}`. `id`는 기본 목록의 고정 번호다.
- 조건에 맞는 메뉴가 없으면 `404` `{"detail": "No matching menu"}`.
- 잘못된 `category`, 정수가 아닌 `exclude_ids`, 101개 이상 `exclude_ids`는 `422`.
- 같은 종류의 내 식당 목록은 화면이 식당 목록(`GET /api/restaurants`)에서 같은 `category`로 찾아 보여 준다.

## 참고

- 자동 문서: 서버 실행 중 `http://127.0.0.1:8100/docs`
