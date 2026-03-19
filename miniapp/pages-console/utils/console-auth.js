const { CONSOLE_PROFILE_STORAGE_KEY, CONSOLE_TOKEN_STORAGE_KEY, API_BASE_URL } = require("../../utils/config")

function syncGlobalConsoleProfile(profile) {
  try {
    const app = getApp()
    if (app && app.globalData) {
      app.globalData.consoleProfile = profile || null
    }
  } catch (_error) {
    // Ignore getApp() failures before the app instance is ready.
  }
}

function saveConsoleToken(token) {
  wx.setStorageSync(CONSOLE_TOKEN_STORAGE_KEY, token)
}

function saveConsoleProfile(profile) {
  wx.setStorageSync(CONSOLE_PROFILE_STORAGE_KEY, profile)
  syncGlobalConsoleProfile(profile)
}

function saveConsoleSession(token, profile) {
  saveConsoleToken(token)
  saveConsoleProfile(profile)
}

function getConsoleAccessToken() {
  return wx.getStorageSync(CONSOLE_TOKEN_STORAGE_KEY) || ""
}

function getConsoleProfile() {
  return wx.getStorageSync(CONSOLE_PROFILE_STORAGE_KEY) || null
}

function clearConsoleSession() {
  wx.removeStorageSync(CONSOLE_TOKEN_STORAGE_KEY)
  wx.removeStorageSync(CONSOLE_PROFILE_STORAGE_KEY)
  syncGlobalConsoleProfile(null)
}

function redirectToConsoleLogin() {
  const pages = getCurrentPages()
  const currentRoute = pages.length ? pages[pages.length - 1].route : ""
  if (currentRoute === "pages-console/login/index") {
    return
  }

  wx.reLaunch({
    url: "/pages-console/login/index",
  })
}

function fetchConsoleProfile(token = getConsoleAccessToken()) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}/admin/auth/me`,
      method: "GET",
      header: {
        Authorization: `Bearer ${token}`,
      },
      success: (response) => {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          saveConsoleProfile(response.data)
          resolve(response.data)
          return
        }
        reject(response)
      },
      fail: reject,
    })
  })
}

function loginConsole(username, password) {
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
            const profile = await fetchConsoleProfile(response.data.access_token)
            saveConsoleSession(response.data.access_token, profile)
            resolve({
              access_token: response.data.access_token,
              profile,
            })
          } catch (error) {
            clearConsoleSession()
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

function ensureConsoleLogin() {
  const token = getConsoleAccessToken()
  const profile = getConsoleProfile()
  if (token && profile) {
    syncGlobalConsoleProfile(profile)
    return Promise.resolve({
      access_token: token,
      profile,
    })
  }
  return Promise.reject(new Error("Console login required"))
}

module.exports = {
  clearConsoleSession,
  ensureConsoleLogin,
  fetchConsoleProfile,
  getConsoleAccessToken,
  getConsoleProfile,
  loginConsole,
  redirectToConsoleLogin,
  saveConsoleProfile,
}
