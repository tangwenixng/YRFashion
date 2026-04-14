import axios from 'axios'

import { apiBaseURL } from './base'
import { adminLoginPath } from '../router/base'

export const TOKEN_STORAGE_KEY = 'yrfasion-admin-token'

export const http = axios.create({
  baseURL: apiBaseURL,
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

      if (window.location.pathname !== adminLoginPath) {
        window.location.href = adminLoginPath
      }
    }

    return Promise.reject(error)
  },
)
