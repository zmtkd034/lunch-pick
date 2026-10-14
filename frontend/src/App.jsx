import { useEffect, useState } from 'react'
import { getErrorMessage, request } from './api.js'
import RestaurantForm from './components/RestaurantForm.jsx'
import RestaurantList from './components/RestaurantList.jsx'
import './App.css'

// L05: 식당 목록과 등록. 데이터는 백엔드 API(/api/restaurants)로만 주고받는다.
export default function App() {
  const [restaurants, setRestaurants] = useState([])
  // "loading" | "ready" | "error". 목록을 불러오지 못하면 빈 목록 안내 대신 오류를 보여 준다.
  const [loadState, setLoadState] = useState('loading')
  const [apiError, setApiError] = useState('')
  // 값을 바꾸면 목록을 서버에서 다시 불러온다.
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    // 응답이 오기 전에 다시 불러오기를 누르면 이전 응답은 쓰지 않는다.
    let ignore = false
    request('GET', '/api/restaurants')
      .then((data) => {
        if (!ignore) {
          setRestaurants(data)
          setLoadState('ready')
          setApiError('')
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

  function reloadRestaurants() {
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

  return (
    <main className="container">
      <h1>오늘 뭐 먹지?</h1>

      {apiError && (
        <div className="api-error" role="alert">
          <span>{apiError}</span>
          <button type="button" onClick={reloadRestaurants}>다시 불러오기</button>
        </div>
      )}

      <RestaurantForm onCreate={handleCreate} />

      <section className="restaurant-section" aria-labelledby="restaurant-list-heading">
        <h2 id="restaurant-list-heading" className="section-title">식당 목록</h2>
        <RestaurantList restaurants={restaurants} loadState={loadState} />
      </section>
    </main>
  )
}
