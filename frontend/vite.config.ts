import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_DEV_API_PROXY_TARGET || 'http://127.0.0.1:8000'
  const devServerHost = env.VITE_DEV_SERVER_HOST || '0.0.0.0'
  const allowedHosts = (env.VITE_DEV_ALLOWED_HOSTS || 'localhost,127.0.0.1,.dadaye.online')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

  return {
    // 使用相对资源路径产出构建文件，兼容 / 与 /fashion/ 这类前缀部署场景。
    base: './',
    plugins: [vue()],
    server: {
      host: devServerHost,
      allowedHosts,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/uploads': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: devServerHost,
    },
  }
})
