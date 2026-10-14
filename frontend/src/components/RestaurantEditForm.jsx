import { useRef, useState } from 'react'
import { ApiError, getErrorMessage } from '../api.js'
import {
  CATEGORIES,
  CATEGORY_LABELS,
  MEMO_MAX_LENGTH,
  PRICE_LABELS,
  PRICE_RANGES,
  validateRestaurantInput,
} from '../constants.js'

// 식당 수정 폼. onSave(value)는 API에 저장하고 실패하면 오류를 던진다.
export default function RestaurantEditForm({ restaurant, onSave, onCancel }) {
  const [form, setForm] = useState({
    name: restaurant.name,
    category: restaurant.category,
    price_range: restaurant.price_range,
    memo: restaurant.memo,
  })
  const [error, setError] = useState('')
  const savingRef = useRef(false)
  const [saving, setSaving] = useState(false)

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    if (savingRef.current) {
      return
    }
    const result = validateRestaurantInput(form)
    if (result.error) {
      setError(result.error)
      return
    }
    savingRef.current = true
    setSaving(true)
    try {
      await onSave(result.value)
    } catch (requestError) {
      // 404는 목록을 새로 불러오며 이 폼이 닫히므로 여기서는 다른 오류만 보여 준다.
      if (!(requestError instanceof ApiError && requestError.status === 404)) {
        // 실패하면 입력값을 그대로 두어 다시 시도할 수 있게 한다.
        setError(getErrorMessage(requestError))
      }
      savingRef.current = false
      setSaving(false)
    }
  }

  return (
    <form className="edit-form" onSubmit={handleSubmit} noValidate>
      <div className="edit-row">
        <input
          className="edit-name"
          type="text"
          aria-label="식당 이름 수정"
          value={form.name}
          onChange={update('name')}
          disabled={saving}
          autoFocus
        />
      </div>
      <div className="edit-row">
        <select aria-label="음식 종류 수정" value={form.category} onChange={update('category')} disabled={saving}>
          {CATEGORIES.map((value) => (
            <option key={value} value={value}>{CATEGORY_LABELS[value]}</option>
          ))}
        </select>
        <select aria-label="가격대 수정" value={form.price_range} onChange={update('price_range')} disabled={saving}>
          {PRICE_RANGES.map((value) => (
            <option key={value} value={value}>{PRICE_LABELS[value]}</option>
          ))}
        </select>
      </div>
      <textarea
        aria-label="메모 수정"
        rows={3}
        maxLength={MEMO_MAX_LENGTH}
        placeholder="메모 (선택, 500자 이하)"
        value={form.memo}
        onChange={update('memo')}
        disabled={saving}
      />
      <div className="edit-row edit-actions">
        <button type="submit" disabled={saving}>저장</button>
        <button type="button" onClick={onCancel} disabled={saving}>취소</button>
      </div>
      <p className="edit-error" role="alert">{error}</p>
    </form>
  )
}
