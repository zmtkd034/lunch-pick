import { useRef, useState } from 'react'
import { getErrorMessage } from '../api.js'
import {
  CATEGORIES,
  CATEGORY_LABELS,
  MEMO_MAX_LENGTH,
  PRICE_LABELS,
  PRICE_RANGES,
  validateRestaurantInput,
} from '../constants.js'

const EMPTY_FORM = { name: '', category: 'ETC', price_range: 'MID', memo: '' }

// 식당 등록 폼. onCreate(value)는 API에 등록하고 실패하면 오류를 던진다.
export default function RestaurantForm({ onCreate }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState('')
  // 요청이 끝나기 전에 다시 제출해도 중복 등록되지 않게 막는다.
  // state는 다음 렌더링 전까지 바뀌지 않으므로, 즉시 바뀌는 ref로 막고 state는 입력칸 비활성화에만 쓴다.
  const submittingRef = useRef(false)
  const [submitting, setSubmitting] = useState(false)

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    if (submittingRef.current) {
      return
    }
    const result = validateRestaurantInput(form)
    if (result.error) {
      setError(result.error)
      return
    }
    submittingRef.current = true
    setSubmitting(true)
    try {
      await onCreate(result.value)
      setForm(EMPTY_FORM)
      setError('')
    } catch (requestError) {
      // 실패하면 입력값을 그대로 두어 다시 시도할 수 있게 한다.
      setError(getErrorMessage(requestError))
    } finally {
      submittingRef.current = false
      setSubmitting(false)
    }
  }

  return (
    <form className="restaurant-form" onSubmit={handleSubmit} noValidate>
      <div className="form-row">
        <label htmlFor="restaurant-name" className="visually-hidden">식당 이름</label>
        <input
          id="restaurant-name"
          type="text"
          placeholder="식당 이름 (1~50자)"
          autoComplete="off"
          value={form.name}
          onChange={update('name')}
          disabled={submitting}
        />
        <button type="submit" disabled={submitting}>등록</button>
      </div>
      <div className="form-row form-options">
        <label>
          음식 종류
          <select value={form.category} onChange={update('category')} disabled={submitting}>
            {CATEGORIES.map((value) => (
              <option key={value} value={value}>{CATEGORY_LABELS[value]}</option>
            ))}
          </select>
        </label>
        <label>
          가격대
          <select value={form.price_range} onChange={update('price_range')} disabled={submitting}>
            {PRICE_RANGES.map((value) => (
              <option key={value} value={value}>{PRICE_LABELS[value]}</option>
            ))}
          </select>
        </label>
      </div>
      <label htmlFor="restaurant-memo" className="visually-hidden">메모</label>
      <textarea
        id="restaurant-memo"
        rows={2}
        maxLength={MEMO_MAX_LENGTH}
        placeholder="메모 (선택, 500자 이하)"
        value={form.memo}
        onChange={update('memo')}
        disabled={submitting}
      />
      <p className="form-error" role="alert">{error}</p>
    </form>
  )
}
