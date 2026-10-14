// 입력 규칙과 표시 이름. 서버(API-SPEC.md)와 같은 규칙이며, 서버도 다시 검사한다.
export const NAME_MAX_LENGTH = 50
export const MEMO_MAX_LENGTH = 500

export const CATEGORIES = ['KOREAN', 'CHINESE', 'JAPANESE', 'WESTERN', 'SNACK', 'ETC']
export const CATEGORY_LABELS = {
  KOREAN: '한식',
  CHINESE: '중식',
  JAPANESE: '일식',
  WESTERN: '양식',
  SNACK: '분식',
  ETC: '기타',
}

export const PRICE_RANGES = ['LOW', 'MID', 'HIGH']
export const PRICE_LABELS = { LOW: '저렴', MID: '보통', HIGH: '비쌈' }

// 등록·수정 입력을 검사해 API로 보낼 값으로 바꾼다. 문제가 있으면 { error }를 돌려준다.
export function validateRestaurantInput(input) {
  const name = input.name.trim()
  if (name.length === 0) {
    return { error: '식당 이름을 입력해 주세요.' }
  }
  if (name.length > NAME_MAX_LENGTH) {
    return { error: `식당 이름은 ${NAME_MAX_LENGTH}자 이하로 입력해 주세요.` }
  }
  if (!CATEGORIES.includes(input.category)) {
    return { error: '음식 종류를 선택해 주세요.' }
  }
  if (!PRICE_RANGES.includes(input.price_range)) {
    return { error: '가격대를 선택해 주세요.' }
  }
  if (input.memo.length > MEMO_MAX_LENGTH) {
    return { error: `메모는 ${MEMO_MAX_LENGTH}자 이하로 입력해 주세요.` }
  }
  return { value: { name, category: input.category, price_range: input.price_range, memo: input.memo } }
}
