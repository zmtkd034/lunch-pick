import { useEffect, useRef, useState } from 'react'
import { ApiError, getErrorMessage, request } from './api.js'
import { getLocalToday, matchesFilters } from './constants.js'
import RestaurantFilters from './components/RestaurantFilters.jsx'
import RestaurantForm from './components/RestaurantForm.jsx'
import RestaurantList from './components/RestaurantList.jsx'
import './App.css'

// L05: 식당 목록과 등록. L06: 검색·필터, 수정·삭제, 먹었어요.
// 데이터는 백엔드 API(/api/restaurants)로만 주고받는다. 검색·필터는 받아 온 목록으로 화면에서 계산한다.
export default function App() {
  const [restaurants, setRestaurants] = useState([])
  // "loading" | "ready" | "error". 목록을 불러오지 못하면 빈 목록 안내 대신 오류를 보여 준다.
  const [loadState, setLoadState] = useState('loading')
  const [apiError, setApiError] = useState('')
  // 값을 바꾸면 목록을 서버에서 다시 불러온다.
  const [reloadKey, setReloadKey] = useState(0)
  // 다시 불러오기에 성공한 뒤 보여 줄 안내(예: 404 후 "목록을 새로 불러왔습니다"). 없으면 배너를 지운다.
  const reloadNoticeRef = useRef('')
  const [filters, setFilters] = useState({ q: '', category: '', price_range: '' })

  useEffect(() => {
    // 응답이 오기 전에 다시 불러오기를 누르면 이전 응답은 쓰지 않는다.
    let ignore = false
    request('GET', '/api/restaurants')
      .then((data) => {
        if (!ignore) {
          setRestaurants(data)
          setLoadState('ready')
          setApiError(reloadNoticeRef.current)
          reloadNoticeRef.current = ''
        }
      })
      .catch((error) => {
        if (!ignore) {
          setLoadState('error')
          setApiError(`식당 목록을 불러오지 못했습니다. ${getErrorMessage(error)}`)
        }
      })
    return () => {
      ignore = true
    }
  }, [reloadKey])

  function reloadRestaurants(notice = '') {
    reloadNoticeRef.current = notice
    setLoadState('loading')
    setReloadKey((key) => key + 1)
  }

  async function handleCreate(value) {
    const created = await request('POST', '/api/restaurants', value)
    if (loadState === 'ready') {
      setRestaurants((current) => [...current, created])
    } else {
      // 처음 목록을 불러오지 못한 상태였다면 서버 목록 전체를 다시 받아 맞춘다.
      reloadRestaurants()
    }
  }

  function replaceRestaurant(updated) {
    setRestaurants((current) => current.map((item) => (item.id === updated.id ? updated : item)))
  }

  // 수정·삭제·먹었어요 대상이 서버에 없으면(404) 목록을 다시 불러와 화면을 맞춘다.
  function showItemError(error) {
    if (error instanceof ApiError && error.status === 404) {
      reloadRestaurants('이미 삭제되었거나 없는 식당입니다. 목록을 새로 불러왔습니다.')
      return
    }
    setApiError(getErrorMessage(error))
  }

  // 수정 실패는 수정 폼이 오류를 보여 주도록 다시 던진다.
  async function handleUpdate(id, value) {
    try {
      replaceRestaurant(await request('PATCH', `/api/restaurants/${id}`, value))
      setApiError('')
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        showItemError(error)
      }
      throw error
    }
  }

  async function handleDelete(id) {
    try {
      await request('DELETE', `/api/restaurants/${id}`)
      setRestaurants((current) => current.filter((item) => item.id !== id))
      setApiError('')
    } catch (error) {
      showItemError(error)
    }
  }

  async function handleVisit(id) {
    try {
      replaceRestaurant(await request('POST', `/api/restaurants/${id}/visit`, { visited_on: getLocalToday() }))
      setApiError('')
    } catch (error) {
      showItemError(error)
    }
  }

  const visibleRestaurants = restaurants.filter((restaurant) => matchesFilters(restaurant, filters))

  return (
    <main className="container">
      <h1>오늘 뭐 먹지?</h1>

      {apiError && (
        <div className="api-error" role="alert">
          <span>{apiError}</span>
          <button type="button" onClick={() => reloadRestaurants()}>다시 불러오기</button>
        </div>
      )}

      <RestaurantForm onCreate={handleCreate} />

      <section className="restaurant-section" aria-labelledby="restaurant-list-heading">
        <h2 id="restaurant-list-heading" className="section-title">식당 목록</h2>
        <RestaurantFilters filters={filters} onChange={setFilters} />
        <RestaurantList
          restaurants={restaurants}
          visibleRestaurants={visibleRestaurants}
          loadState={loadState}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
          onVisit={handleVisit}
        />
      </section>
    </main>
  )
}
