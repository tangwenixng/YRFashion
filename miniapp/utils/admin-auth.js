const { ADMIN_PROFILE_STORAGE_KEY, ADMIN_TOKEN_STORAGE_KEY, API_BASE_URL } = require("./config")

function syncGlobalAdminProfile(profile) {
  try {
    const app = getApp()
    if (app && app.globalData) {
      app.globalData.adminProfile = profile || null
    }
  } catch (_error) {
    // Ignore getApp() failures before the app instance is ready.
  }
}

function saveAdminToken(token) {
  wx.setStorageSync(ADMIN_TOKEN_STORAGE_KEY, token)
}

function saveAdminProfile(profile) {
  wx.setStorageSync(ADMIN_PROFILE_STORAGE_KEY, profile)
  syncGlobalAdminProfile(profile)
}

function saveAdminSession(token, profile) {
  saveAdminToken(token)
  saveAdminProfile(profile)
}

function getAdminAccessToken() {
  return wx.getStorageSync(ADMIN_TOKEN_STORAGE_KEY) || ""
}

function getAdminProfile() {
  return wx.getStorageSync(ADMIN_PROFILE_STORAGE_KEY) || null
}

function clearAdminSession() {
  wx.removeStorageSync(ADMIN_TOKEN_STORAGE_KEY)
  wx.removeStorageSync(ADMIN_PROFILE_STORAGE_KEY)
  syncGlobalAdminProfile(null)
}

function redirectToAdminLogin() {
  const pages = getCurrentPages()
  const currentRoute = pages.length ? pages[pages.length - 1].route : ""
  if (currentRoute === "pages-admin/login/index") {
    return
  }

  wx.reLaunch({
    url: "/pages-admin/login/index",
  })
}

function fetchAdminProfile(token = getAdminAccessToken()) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}/admin/auth/me`,
      method: "GET",
      header: {
        Authorization: `Bearer ${token}`,
      },
      success: (response) => {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          saveAdminProfile(response.data)
          resolve(response.data)
          return
        }
        reject(response)
      },
      fail: reject,
    })
  })
}

function loginAdmin(username, password) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}/admin/auth/login`,
      method: "POST",
      data: {
        username,
        password,
      },
      success: async (response) => {
        if (response.statusCode >= 200 && response.statusCode < 300 && response.data.access_token) {
          try {
            const profile = await fetchAdminProfile(response.data.access_token)
            saveAdminSession(response.data.access_token, profile)
            resolve({
              access_token: response.data.access_token,
              profile,
            })
          } catch (error) {
            clearAdminSession()
            reject(error)
          }
          return
        }
        reject(response)
      },
      fail: reject,
    })
  })
}

function ensureAdminLogin() {
  const token = getAdminAccessToken()
  const profile = getAdminProfile()
  if (token && profile) {
    syncGlobalAdminProfile(profile)
    return Promise.resolve({
      access_token: token,
      profile,
    })
  }
  return Promise.reject(new Error("Admin login required"))
}

module.exports = {
  clearAdminSession,
  ensureAdminLogin,
  fetchAdminProfile,
  getAdminAccessToken,
  getAdminProfile,
  loginAdmin,
  redirectToAdminLogin,
  saveAdminProfile,
}
