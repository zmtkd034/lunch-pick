// 백엔드 API 호출. 화면과 같은 주소의 /api를 부른다(개발: Vite가 8100으로 전달).
export class ApiError extends Error {
  constructor(status) {
    super(`API error ${status}`)
    // 0은 서버에 연결하지 못한 경우다.
    this.status = status
  }
}

export async function request(method, path, body) {
  const options = { method }
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  let response
  try {
    response = await fetch(path, options)
  } catch {
    throw new ApiError(0)
  }
  if (!response.ok) {
    throw new ApiError(response.status)
  }
  return response.status === 204 ? null : response.json()
}

export function getErrorMessage(error) {
  if (!(error instanceof ApiError) || error.status === 0 || error.status === 502 || error.status === 504) {
    return 'API 서버에 연결할 수 없습니다. 서버가 켜져 있는지 확인해 주세요.'
  }
  if (error.status === 404) {
    return '이미 삭제되었거나 없는 식당입니다.'
  }
  if (error.status === 422) {
    return '입력값이 올바르지 않아 서버가 거절했습니다.'
  }
  if (error.status === 503) {
    return 'DB에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.'
  }
  return `서버 오류가 발생했습니다(${error.status}). 잠시 후 다시 시도해 주세요.`
}
