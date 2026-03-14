import axios from 'axios'

export const TOKEN_STORAGE_KEY = 'yrfasion-admin-token'

const configuredBaseURL = (import.meta.env.VITE_API_BASE_URL || '/api').trim()
const normalizedBaseURL = configuredBaseURL
  ? configuredBaseURL.replace(/\/$/, '')
  : '/api'

export const http = axios.create({
  baseURL: normalizedBaseURL,
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY)

      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  },
)
