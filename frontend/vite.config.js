import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 前端开发服务器；接口基地址通过 VITE_API_BASE 注入（默认见 src/api/client.js）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1',
  },
})
