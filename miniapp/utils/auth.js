const { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } = require("./config")

function saveSession(session) {
  wx.setStorageSync(TOKEN_STORAGE_KEY, session.access_token)
  wx.setStorageSync(USER_STORAGE_KEY, session.user)
}

function getAccessToken() {
  return wx.getStorageSync(TOKEN_STORAGE_KEY) || ""
}

function getMiniappUser() {
  return wx.getStorageSync(USER_STORAGE_KEY) || null
}

function clearSession() {
  wx.removeStorageSync(TOKEN_STORAGE_KEY)
  wx.removeStorageSync(USER_STORAGE_KEY)
}

function loginWithCode(code) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${require("./config").API_BASE_URL}/miniapp/auth/login`,
      method: "POST",
      data: { code },
      success: (response) => {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          saveSession(response.data)
          resolve(response.data)
          return
        }
        reject(response)
      },
      fail: reject,
    })
  })
}

function ensureMiniappLogin(force = false) {
  if (!force) {
    const token = getAccessToken()
    const user = getMiniappUser()
    if (token && user) {
      return Promise.resolve({ access_token: token, user })
    }
  }

  return new Promise((resolve, reject) => {
    wx.login({
      success: ({ code }) => {
        if (!code) {
          reject(new Error("wx.login did not return code"))
          return
        }
        loginWithCode(code).then(resolve).catch(reject)
      },
      fail: reject,
    })
  })
}

module.exports = {
  ensureMiniappLogin,
  getAccessToken,
  getMiniappUser,
  clearSession,
}
