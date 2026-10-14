import { useRef, useState } from 'react'
import { ApiError, getErrorMessage, request } from '../api.js'
import CardBack from './CardBack.jsx'
import RevealName from './RevealName.jsx'
import {
  CATEGORIES,
  CATEGORY_LABELS,
  EXCLUDE_DAYS_MAX,
  EXCLUDE_IDS_MAX,
  PREFERENCE_LABELS,
  PRICE_LABELS,
  PRICE_RANGES,
  getLocalToday,
} from '../constants.js'

// 카드를 섞는 연출 시간. 응답이 빨라도 이만큼은 섞은 뒤 카드를 뒤집는다.
const SHUFFLE_MS = 700

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

// L07: 조건을 고르고 카드를 뽑아 식당 하나를 무작위로 추천받는다.
// L10: 별로 표시한 식당 빼기, 결과를 패스하고 그 식당을 뺀 채 다시 뽑기.
// onPicked(restaurant)는 뽑힌 식당을 목록에 반영하고, onVisit(id)는 먹었어요를 기록한다.
export default function RecommendPanel({ restaurants, onPicked, onVisit }) {
  const [categories, setCategories] = useState([])
  const [priceRanges, setPriceRanges] = useState([])
  const [excludeDays, setExcludeDays] = useState('0')
  const [excludeDisliked, setExcludeDisliked] = useState(true)
  // 이번 조건에서 패스한 식당 id. 화면에서만 유지하며 조건을 바꾸면 비운다.
  const [passedIds, setPassedIds] = useState([])
  // "idle" | "drawing" | "revealed" | "empty"
  const [phase, setPhase] = useState('idle')
  const [pickedId, setPickedId] = useState(null)
  // 결과를 보여 줄 때마다 1씩 늘려 이름 강조 애니메이션을 다시 재생한다(L22).
  const [revealCount, setRevealCount] = useState(0)
  const [error, setError] = useState('')
  // 뽑는 중에 다시 눌러도 요청이 겹치지 않게 막는다.
  const drawingRef = useRef(false)
  const [visiting, setVisiting] = useState(false)

  // 뽑힌 식당은 목록에서 찾아 보여 준다. 목록에서 수정·먹었어요가 바로 반영되고, 삭제되면 카드를 닫는다.
  const picked = restaurants.find((restaurant) => restaurant.id === pickedId) ?? null
  const shownPhase = phase === 'revealed' && picked === null ? 'idle' : phase

  // 조건이 바뀌면 이전 조건에서 패스한 목록은 의미가 없으므로 비운다.
  const toggle = (list, setList, value) => {
    setList(list.includes(value) ? list.filter((item) => item !== value) : [...list, value])
    setPassedIds([])
  }

  // excludeIds: 이번 요청에서 뺄 식당 id. 패스 직후에는 state가 아직 바뀌지 않았으므로 직접 넘긴다.
  async function draw(excludeIds = passedIds) {
    if (drawingRef.current) {
      return
    }
    const days = Number(excludeDays)
    if (excludeDays.trim() === '' || !Number.isInteger(days) || days < 0 || days > EXCLUDE_DAYS_MAX) {
      setError(`최근 방문 제외 일수는 0~${EXCLUDE_DAYS_MAX} 사이의 정수로 입력해 주세요.`)
      return
    }
    drawingRef.current = true
    setError('')
    setPhase('drawing')

    const params = new URLSearchParams()
    categories.forEach((value) => params.append('category', value))
    priceRanges.forEach((value) => params.append('price_range', value))
    params.set('exclude_days', String(days))
    params.set('today', getLocalToday())
    params.set('exclude_disliked', String(excludeDisliked))
    excludeIds.forEach((id) => params.append('exclude_ids', String(id)))
    const shuffle = new Promise((resolve) => setTimeout(resolve, prefersReducedMotion() ? 0 : SHUFFLE_MS))

    try {
      const [result] = await Promise.all([request('GET', `/api/recommendation?${params}`), shuffle])
      onPicked(result)
      setPickedId(result.id)
      setRevealCount((count) => count + 1)
      setPhase('revealed')
    } catch (requestError) {
      await shuffle
      setPickedId(null)
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

  async function visit() {
    // 카드를 섞는 중에는 화면에서 사라진 이전 결과에 방문 기록을 남기지 않는다(L20).
    if (visiting || picked === null || drawingRef.current) {
      return
    }
    setVisiting(true)
    try {
      await onVisit(picked.id)
    } finally {
      setVisiting(false)
    }
  }

  function pass() {
    if (picked === null || drawingRef.current) {
      return
    }
    // 서버가 받는 개수를 넘지 않게 가장 최근에 패스한 것만 남긴다.
    const next = [...passedIds.filter((id) => id !== picked.id), picked.id].slice(-EXCLUDE_IDS_MAX)
    setPassedIds(next)
    draw(next)
  }

  function resetPassed() {
    setPassedIds([])
    if (shownPhase === 'empty') {
      setPhase('idle')
    }
  }

  const drawing = shownPhase === 'drawing'

  return (
    <div className="recommend-panel">
      <fieldset className="choice-group" disabled={drawing}>
        <legend>음식 종류 (선택 안 하면 전체)</legend>
        {CATEGORIES.map((value) => (
          <label key={value} className="chip">
            <input
              type="checkbox"
              name="recommend-category"
              value={value}
              checked={categories.includes(value)}
              onChange={() => toggle(categories, setCategories, value)}
            />
            <span>{CATEGORY_LABELS[value]}</span>
          </label>
        ))}
      </fieldset>

      <fieldset className="choice-group" disabled={drawing}>
        <legend>가격대 (선택 안 하면 전체)</legend>
        {PRICE_RANGES.map((value) => (
          <label key={value} className="chip">
            <input
              type="checkbox"
              name="recommend-price"
              value={value}
              checked={priceRanges.includes(value)}
              onChange={() => toggle(priceRanges, setPriceRanges, value)}
            />
            <span>{PRICE_LABELS[value]}</span>
          </label>
        ))}
      </fieldset>

      <div className="recommend-row">
        <label className="exclude-days">
          최근
          <input
            id="exclude-days"
            type="number"
            inputMode="numeric"
            min={0}
            max={EXCLUDE_DAYS_MAX}
            step={1}
            value={excludeDays}
            onChange={(event) => {
              setExcludeDays(event.target.value)
              setPassedIds([])
            }}
            disabled={drawing}
          />
          일 안에 간 곳 빼기 (0이면 안 뺌)
        </label>
        <label className="exclude-disliked">
          <input
            type="checkbox"
            checked={excludeDisliked}
            onChange={(event) => {
              setExcludeDisliked(event.target.checked)
              setPassedIds([])
            }}
            disabled={drawing}
          />
          별로 표시한 식당 빼기
        </label>
        <button type="button" className="draw-button" onClick={() => draw()} disabled={drawing}>
          {drawing ? '카드 섞는 중…' : shownPhase === 'revealed' ? '다시 뽑기' : '카드 뽑기'}
        </button>
      </div>
      <p className="form-error" role="alert">{error}</p>

      <div className="card-stage">
        <div
          className={`draw-card${shownPhase === 'revealed' ? ' is-flipped' : ''}${drawing ? ' is-shuffling' : ''}`}
          data-phase={shownPhase}
        >
          <div className="card-inner">
            <CardBack hidden={shownPhase === 'revealed'} />
            {/* 뒤집혀 숨은 앞면(섞는 중·결과 없음)은 inert로 눌리지도 초점이 가지도 않게 한다(L20). */}
            <div
              className="card-face card-front"
              aria-hidden={shownPhase !== 'revealed'}
              inert={shownPhase !== 'revealed'}
            >
              {picked && (
                <>
                  <span className="card-label">오늘은 여기!</span>
                  <RevealName key={revealCount} name={picked.name} />
                  <div className="restaurant-meta">
                    <span className="badge">{CATEGORY_LABELS[picked.category]}</span>
                    <span className={`badge price-${picked.price_range.toLowerCase()}`}>
                      {PRICE_LABELS[picked.price_range]}
                    </span>
                    {picked.preference && (
                      <span className={`badge pref-${picked.preference.toLowerCase()}`}>
                        {PREFERENCE_LABELS[picked.preference]}
                      </span>
                    )}
                    <span className="badge visited">
                      {picked.last_visited_on ? `마지막 방문 ${picked.last_visited_on}` : '방문 기록 없음'}
                    </span>
                  </div>
                  {picked.memo !== '' && <p className="card-memo">{picked.memo}</p>}
                  <div className="card-actions">
                    <button type="button" className="card-visit" onClick={visit} disabled={visiting}>
                      먹었어요
                    </button>
                    <button type="button" className="card-pass" onClick={pass} disabled={visiting}>
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
        {shownPhase === 'empty' && '조건에 맞는 식당이 없습니다. 조건을 바꾸거나 식당을 더 등록해 보세요.'}
        {shownPhase === 'revealed' && picked && `추천 결과: ${picked.name}`}
      </p>
      {passedIds.length > 0 && (
        <p className="passed-info">
          패스한 식당 {passedIds.length}곳은 빼고 뽑는 중
          <button type="button" className="link-button" onClick={resetPassed} disabled={drawing}>
            패스 초기화
          </button>
        </p>
      )}
    </div>
  )
}
