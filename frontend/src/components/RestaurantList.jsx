import { CATEGORY_LABELS, PRICE_LABELS } from '../constants.js'

// 식당 목록. 사용자 입력(이름·메모)은 React가 글자로만 표시한다(HTML로 해석하지 않음).
export default function RestaurantList({ restaurants, loadState }) {
  if (loadState === 'loading') {
    return <p className="empty-message">식당 목록을 불러오는 중입니다…</p>
  }
  if (loadState === 'error') {
    return null
  }
  if (restaurants.length === 0) {
    return <p className="empty-message">등록된 식당이 없습니다. 자주 가는 식당을 등록해 보세요.</p>
  }
  return (
    <ul className="restaurant-list">
      {restaurants.map((restaurant) => (
        <li key={restaurant.id} className="restaurant-item" data-id={restaurant.id}>
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
        </li>
      ))}
    </ul>
  )
}
