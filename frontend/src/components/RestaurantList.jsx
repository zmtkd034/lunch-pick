import { useState } from 'react'
import { CATEGORY_LABELS, PRICE_LABELS } from '../constants.js'
import RestaurantEditForm from './RestaurantEditForm.jsx'

// 식당 목록. 사용자 입력(이름·메모)은 React가 글자로만 표시한다(HTML로 해석하지 않음).
// 수정·삭제·먹었어요는 화면 순번이 아닌 식당 id로 처리한다.
export default function RestaurantList({ restaurants, visibleRestaurants, loadState, onUpdate, onDelete, onVisit }) {
  // 수정 중인 식당 id. 한 번에 하나만 수정한다.
  const [editingId, setEditingId] = useState(null)
  // 요청 중인 식당 id. 요청이 끝날 때까지 그 항목의 버튼을 막는다.
  const [busyId, setBusyId] = useState(null)

  if (loadState === 'loading') {
    return <p className="empty-message">식당 목록을 불러오는 중입니다…</p>
  }
  if (loadState === 'error') {
    return null
  }
  if (restaurants.length === 0) {
    return <p className="empty-message">등록된 식당이 없습니다. 자주 가는 식당을 등록해 보세요.</p>
  }
  if (visibleRestaurants.length === 0) {
    return <p className="empty-message">조건에 맞는 식당이 없습니다.</p>
  }

  async function runAction(id, action) {
    if (busyId !== null) {
      return
    }
    setBusyId(id)
    try {
      await action()
    } finally {
      setBusyId(null)
    }
  }

  function handleDelete(restaurant) {
    if (!window.confirm(`"${restaurant.name}" 식당을 삭제할까요?`)) {
      return
    }
    runAction(restaurant.id, async () => {
      await onDelete(restaurant.id)
      if (editingId === restaurant.id) {
        setEditingId(null)
      }
    })
  }

  return (
    <ul className="restaurant-list">
      {visibleRestaurants.map((restaurant) => {
        const busy = busyId === restaurant.id
        return (
          <li key={restaurant.id} className="restaurant-item" data-id={restaurant.id}>
            {editingId === restaurant.id ? (
              <RestaurantEditForm
                restaurant={restaurant}
                onSave={async (value) => {
                  await onUpdate(restaurant.id, value)
                  setEditingId(null)
                }}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <>
                <div className="restaurant-main">
                  <span className="restaurant-name">{restaurant.name}</span>
                  <div className="restaurant-meta">
                    <span className="badge">{CATEGORY_LABELS[restaurant.category]}</span>
                    <span className={`badge price-${restaurant.price_range.toLowerCase()}`}>
                      {PRICE_LABELS[restaurant.price_range]}
                    </span>
                    <span className="badge visited">
                      {restaurant.last_visited_on ? `마지막 방문 ${restaurant.last_visited_on}` : '방문 기록 없음'}
                    </span>
                  </div>
                  {restaurant.memo !== '' && <p className="restaurant-memo">{restaurant.memo}</p>}
                </div>
                <div className="restaurant-actions">
                  <button type="button" data-action="visit" disabled={busy} onClick={() => runAction(restaurant.id, () => onVisit(restaurant.id))}>
                    먹었어요
                  </button>
                  <button type="button" data-action="edit" disabled={busy} onClick={() => setEditingId(restaurant.id)}>
                    수정
                  </button>
                  <button type="button" data-action="delete" disabled={busy} onClick={() => handleDelete(restaurant)}>
                    삭제
                  </button>
                </div>
              </>
            )}
          </li>
        )
      })}
    </ul>
  )
}
