/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_APP_BUILD_TIME?: string
  readonly VITE_DEV_API_PROXY_TARGET?: string
  readonly VITE_DEV_SERVER_HOST?: string
  readonly VITE_DEV_ALLOWED_HOSTS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
