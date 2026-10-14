import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// 개발 서버(5173)는 화면만 제공하고, /api 요청은 백엔드(FastAPI, 8100)로 전달한다.
// 화면 코드에는 DB 접속 정보가 없으며 API만 호출한다.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8100',
    },
  },
})
