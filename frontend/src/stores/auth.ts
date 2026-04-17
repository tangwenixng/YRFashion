import { defineStore } from 'pinia'

import { fetchAdminProfile, loginAdmin, type AdminProfile } from '../api/modules/auth'
import { TOKEN_STORAGE_KEY } from '../api/http'
import { clearAdminExperienceOverride } from '../router/deviceExperience'

interface AuthState {
  token: string
  profile: AdminProfile | null
  initialized: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: window.localStorage.getItem(TOKEN_STORAGE_KEY) ?? '',
    profile: null,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    async initialize() {
      if (!this.token) {
        this.initialized = true
        return
      }

      try {
        this.profile = await fetchAdminProfile()
      } catch {
        this.clearSession({ preserveExperienceOverride: true })
      } finally {
        this.initialized = true
      }
    },
    async login(username: string, password: string) {
      const result = await loginAdmin({ username, password })
      this.token = result.access_token
      window.localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token)
      this.profile = await fetchAdminProfile()
      this.initialized = true
    },
    clearSession(options: { preserveExperienceOverride?: boolean } = {}) {
      this.token = ''
      this.profile = null
      this.initialized = true
      window.localStorage.removeItem(TOKEN_STORAGE_KEY)
      if (!options.preserveExperienceOverride) {
        clearAdminExperienceOverride()
      }
    },
  },
})
