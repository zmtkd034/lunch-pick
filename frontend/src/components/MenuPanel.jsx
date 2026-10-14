import { useRef, useState } from 'react'
import { ApiError, getErrorMessage, request } from '../api.js'
import CardBack from './CardBack.jsx'
import { CATEGORIES, CATEGORY_LABELS, EXCLUDE_IDS_MAX } from '../constants.js'

// 카드를 섞는 연출 시간. 식당 뽑기와 같다.
const SHUFFLE_MS = 700

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

// L12: 식당을 등록하지 않아도 기본 메뉴 목록에서 메뉴를 뽑는다(PRD R14~R16).
// 결과에는 같은 음식 종류로 등록한 내 식당을 함께 보여 준다(종류 기준 연결).
export default function MenuPanel({ restaurants }) {
  const [categories, setCategories] = useState([])
  // "idle" | "drawing" | "revealed" | "empty"
  const [phase, setPhase] = useState('idle')
  const [menu, setMenu] = useState(null)
  const [error, setError] = useState('')
  // 이번 조건에서 패스한 메뉴 id. 화면에서만 유지하며 조건을 바꾸면 비운다.
  const [passedIds, setPassedIds] = useState([])
  const drawingRef = useRef(false)

  const sameCategory = menu ? restaurants.filter((restaurant) => restaurant.category === menu.category) : []

  function toggle(value) {
    setCategories(categories.includes(value) ? categories.filter((item) => item !== value) : [...categories, value])
    setPassedIds([])
  }

  async function draw(excludeIds = passedIds) {
    if (drawingRef.current) {
      return
    }
    drawingRef.current = true
    setError('')
    setPhase('drawing')
    const params = new URLSearchParams()
    categories.forEach((value) => params.append('category', value))
    excludeIds.forEach((id) => params.append('exclude_ids', String(id)))
    const shuffle = new Promise((resolve) => setTimeout(resolve, prefersReducedMotion() ? 0 : SHUFFLE_MS))
    try {
      const [result] = await Promise.all([request('GET', `/api/menu-recommendation?${params}`), shuffle])
      setMenu(result)
      setPhase('revealed')
    } catch (requestError) {
      await shuffle
      setMenu(null)
      if (requestError instanceof ApiError && requestError.status === 404) {
        setPhase('empty')
      } else {
        setPhase('idle')
        setError(getErrorMessage(requestError))
      }
    } finally {
      drawingRef.current = false
    }
  }

  function pass() {
    if (menu === null || drawingRef.current) {
      return
    }
    const next = [...passedIds.filter((id) => id !== menu.id), menu.id].slice(-EXCLUDE_IDS_MAX)
    setPassedIds(next)
    draw(next)
  }

  function resetPassed() {
    setPassedIds([])
    if (phase === 'empty') {
      setPhase('idle')
    }
  }

  const drawing = phase === 'drawing'

  return (
    <div className="menu-panel">
      <fieldset className="choice-group" disabled={drawing}>
        <legend>음식 종류 (선택 안 하면 전체)</legend>
        {CATEGORIES.map((value) => (
          <label key={value} className="chip">
            <input
              type="checkbox"
              name="menu-category"
              value={value}
              checked={categories.includes(value)}
              onChange={() => toggle(value)}
            />
            <span>{CATEGORY_LABELS[value]}</span>
          </label>
        ))}
      </fieldset>

      <div className="recommend-row">
        <span className="menu-hint">등록한 식당이 없어도 메뉴를 골라 드려요.</span>
        <button type="button" className="draw-button" onClick={() => draw()} disabled={drawing}>
          {drawing ? '카드 섞는 중…' : phase === 'revealed' ? '다시 뽑기' : '메뉴 뽑기'}
        </button>
      </div>
      <p className="form-error" role="alert">{error}</p>

      <div className="card-stage">
        <div
          className={`draw-card${phase === 'revealed' ? ' is-flipped' : ''}${drawing ? ' is-shuffling' : ''}`}
          data-phase={phase}
        >
          <div className="card-inner">
            <CardBack hidden={phase === 'revealed'} />
            <div className="card-face card-front" aria-hidden={phase !== 'revealed'}>
              {menu && (
                <>
                  <span className="card-label">오늘의 메뉴!</span>
                  <strong className="card-name">{menu.name}</strong>
                  <div className="restaurant-meta">
                    <span className="badge">{CATEGORY_LABELS[menu.category]}</span>
                  </div>
                  <div className="card-actions">
                    <button type="button" className="card-pass" onClick={pass}>
                      패스
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <p className="recommend-message" role="status">
        {phase === 'empty' && '조건에 맞는 메뉴가 없습니다. 음식 종류를 바꿔 보세요.'}
        {phase === 'revealed' && menu && `추천 메뉴: ${menu.name} (${CATEGORY_LABELS[menu.category]})`}
      </p>
      {phase === 'revealed' && menu && (
        <div className="same-category">
          <p className="same-category-title">내 식당 중 {CATEGORY_LABELS[menu.category]}</p>
          {sameCategory.length > 0 ? (
            <ul className="same-category-list">
              {sameCategory.map((restaurant) => (
                <li key={restaurant.id}>{restaurant.name}</li>
              ))}
            </ul>
          ) : (
            <p className="same-category-empty">
              {CATEGORY_LABELS[menu.category]} 종류로 등록한 식당이 없습니다. 아래에서 식당을 등록해 보세요.
            </p>
          )}
        </div>
      )}
      {passedIds.length > 0 && (
        <p className="passed-info">
          패스한 메뉴 {passedIds.length}개는 빼고 뽑는 중
          <button type="button" className="link-button" onClick={resetPassed} disabled={drawing}>
            패스 초기화
          </button>
        </p>
      )}
    </div>
  )
}
