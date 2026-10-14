import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// 화면 계층은 화면 파일만 제공하고, /api 요청은 애플리케이션 계층(FastAPI, 8100)으로 전달한다.
// 화면 코드에는 DB 접속 정보가 없으며 API만 호출한다.
const API_TARGET = 'http://127.0.0.1:8100'

export default defineConfig({
  plugins: [react()],
  // 개발 서버(npm run dev): 코드 수정이 바로 반영된다.
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: { '/api': API_TARGET },
  },
  // 빌드본 제공(npm run build 후 npm run preview): dist/의 빌드 결과만 제공한다.
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
    proxy: { '/api': API_TARGET },
  },
})
