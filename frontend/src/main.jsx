import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// L16: 제목용 글씨체(주아체, SIL OFL 1.1). 앱에 포함해 외부 사이트에서 불러오지 않는다.
import '@fontsource/jua/400.css'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
