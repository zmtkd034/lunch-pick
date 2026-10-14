# 오늘 뭐 먹지? API 명세

PRD의 요구사항(R01~R10)을 API로 옮긴 계약이다. 구현 순서는 PLAN을 따른다.

| 엔드포인트 | 구현 작업 |
|---|---|
| `GET /api/health` | L01 |
| `GET /api/restaurants`, `POST /api/restaurants` | L02 |
| `PATCH /api/restaurants/{id}`, `DELETE /api/restaurants/{id}`, `POST /api/restaurants/{id}/visit` | L03 |
| `GET /api/recommendation` | L04 |

## 공통

- 기본 주소(개발): `http://127.0.0.1:8100`. 화면 개발 서버(5173)는 `/api` 요청을 이 주소로 전달한다(L05).
- 모든 경로는 `/api`로 시작한다. 요청·응답 본문은 JSON(UTF-8)이다.
- 인증은 없다(로그인 없는 개인용 첫 버전).
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
| `last_visited_on` | string \| null | 마지막 방문일 `YYYY-MM-DD`. 방문 기록 API로만 바꾼다. | `null` |
| `created_at` | string | 서버가 기록하는 등록 시각(ISO 8601, UTC) | 서버 기록 |

```json
{
  "id": 1,
  "name": "김밥천국 역삼점",
  "category": "SNACK",
  "price_range": "LOW",
  "memo": "라볶이 맛있음",
  "last_visited_on": "2026-10-10",
  "created_at": "2026-10-14T06:30:00Z"
}
```

- `id`, `created_at`, `last_visited_on`과 정의되지 않은 필드를 등록·수정 요청으로 보내면 422로 거절한다.

## 오류 응답

| 상태 코드 | 상황 |
|---|---|
| `404 Not Found` | 해당 `id`의 식당이 없음(`{"detail": "Restaurant not found"}`), 추천 조건에 맞는 식당이 없음(`{"detail": "No matching restaurant"}`) |
| `422 Unprocessable Entity` | 입력 규칙 위반(빈 이름, 51자 이름, 501자 메모, 잘못된 종류·가격대·날짜, 정의되지 않은 필드 등). `detail`은 위반 항목 목록(FastAPI 기본 형식) |
| `503 Service Unavailable` | DB에 연결할 수 없음. `{"detail": "Database unavailable"}`, 접속 정보 등 내부 오류는 보여 주지 않는다. |

## 엔드포인트

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

- 바꿀 수 있는 필드: `name`, `category`, `price_range`, `memo`. 이 필드들에 `null`은 보낼 수 없다(422).
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

- `visited_on`은 필수이며 실제 존재하는 `YYYY-MM-DD` 날짜다.
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
| `today` | 사용자 PC의 로컬 날짜 `YYYY-MM-DD`. `exclude_days`가 1 이상이면 필수. |

- 최근 N일 안 방문: `last_visited_on`이 `today - (N - 1)`일부터 `today`까지인 식당. 예: N=1이면 오늘 방문한 곳, N=7이면 오늘 포함 7일 안에 방문한 곳을 뺀다. 방문 기록이 없는 식당은 빼지 않는다.
- 응답 `200 OK`: Restaurant 하나.
- 조건에 맞는 식당이 없으면 `404` `{"detail": "No matching restaurant"}`.
- 잘못된 값(종류·가격대·범위 밖 `exclude_days`·잘못된 날짜·`today` 누락)은 `422`.

## 참고

- 자동 문서: 서버 실행 중 `http://127.0.0.1:8100/docs`
