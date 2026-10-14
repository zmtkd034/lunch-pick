import { useState } from 'react'
import MenuPanel from './MenuPanel.jsx'
import RecommendPanel from './RecommendPanel.jsx'

const MODES = [
  { value: 'restaurant', label: '식당 뽑기' },
  { value: 'menu', label: '메뉴 뽑기' },
]

// L12: 식당 뽑기와 메뉴 뽑기를 전환한다. 전환하면 패널이 새로 만들어져 카드·패스 목록이 초기화된다.
export default function RecommendSection({ restaurants, onPicked, onVisit }) {
  const [mode, setMode] = useState('restaurant')
  return (
    <section className="menu-board recommend" aria-labelledby="recommend-heading">
      <h2 id="recommend-heading" className="section-title">카드 뽑기 추천</h2>
      <div className="mode-tabs" role="group" aria-label="추천 방식">
        {MODES.map((item) => (
          <button
            key={item.value}
            type="button"
            className="mode-tab"
            data-mode={item.value}
            aria-pressed={mode === item.value}
            onClick={() => setMode(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {mode === 'restaurant' ? (
        <RecommendPanel restaurants={restaurants} onPicked={onPicked} onVisit={onVisit} />
      ) : (
        <MenuPanel restaurants={restaurants} />
      )}
    </section>
  )
}
