import { CATEGORIES, CATEGORY_LABELS, PRICE_LABELS, PRICE_RANGES } from '../constants.js'

// 이름 검색, 음식 종류, 가격대 필터. 세 조건을 모두 만족하는 식당만 보여 준다(AND).
export default function RestaurantFilters({ filters, onChange }) {
  const update = (field) => (event) => onChange({ ...filters, [field]: event.target.value })
  return (
    <div className="filters" role="search">
      <label htmlFor="filter-search" className="visually-hidden">이름 검색</label>
      <input
        id="filter-search"
        type="search"
        placeholder="이름 검색"
        autoComplete="off"
        value={filters.q}
        onChange={update('q')}
      />
      <label htmlFor="filter-category" className="visually-hidden">음식 종류 필터</label>
      <select id="filter-category" value={filters.category} onChange={update('category')}>
        <option value="">모든 종류</option>
        {CATEGORIES.map((value) => (
          <option key={value} value={value}>{CATEGORY_LABELS[value]}</option>
        ))}
      </select>
      <label htmlFor="filter-price" className="visually-hidden">가격대 필터</label>
      <select id="filter-price" value={filters.price_range} onChange={update('price_range')}>
        <option value="">모든 가격대</option>
        {PRICE_RANGES.map((value) => (
          <option key={value} value={value}>{PRICE_LABELS[value]}</option>
        ))}
      </select>
    </div>
  )
}
