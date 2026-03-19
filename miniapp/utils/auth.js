const { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } = require("./config")

function syncGlobalMiniappUser(user) {
  try {
    const app = getApp()
    if (app && app.globalData) {
      app.globalData.miniappUser = user || null
    }
  } catch (_error) {
    // Ignore getApp() failures before the app instance is ready.
  }
}

function saveSession(session) {
  wx.setStorageSync(TOKEN_STORAGE_KEY, session.access_token)
  wx.setStorageSync(USER_STORAGE_KEY, session.user)
  syncGlobalMiniappUser(session.user)
}

function saveMiniappUser(user) {
  wx.setStorageSync(USER_STORAGE_KEY, user)
  syncGlobalMiniappUser(user)
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
  syncGlobalMiniappUser(null)
}

function isTemporaryMiniappFilePath(value) {
  if (!value || typeof value !== "string") {
    return false
  }

  return /^wxfile:\/\//i.test(value) || /^https?:\/\/(tmp|usr)\//i.test(value)
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

function fetchMiniappProfile() {
  const token = getAccessToken()
  if (!token) {
    return ensureMiniappLogin(true).then(() => fetchMiniappProfile())
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${require("./config").API_BASE_URL}/miniapp/auth/profile`,
      method: "GET",
      header: {
        Authorization: `Bearer ${token}`,
      },
      success: (response) => {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          saveMiniappUser(response.data)
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

function uploadMiniappAvatar(filePath) {
  const token = getAccessToken()
  if (!token) {
    return ensureMiniappLogin().then(() => uploadMiniappAvatar(filePath))
  }

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${require("./config").API_BASE_URL}/miniapp/auth/avatar`,
      filePath,
      name: "file",
      header: {
        Authorization: `Bearer ${token}`,
      },
      success: (response) => {
        let payload = {}
        try {
          payload = JSON.parse(response.data || "{}")
        } catch (_error) {
          reject(new Error("Failed to parse avatar upload response"))
          return
        }

        if (response.statusCode >= 200 && response.statusCode < 300 && payload.avatar_url) {
          resolve(payload.avatar_url)
          return
        }

        reject(payload)
      },
      fail: reject,
    })
  })
}

function updateMiniappProfile(payload) {
  const send = (finalPayload) =>
    new Promise((resolve, reject) => {
      wx.request({
        url: `${require("./config").API_BASE_URL}/miniapp/auth/profile`,
        method: "PUT",
        data: finalPayload,
        header: {
          Authorization: `Bearer ${getAccessToken()}`,
        },
        success: (response) => {
          if (response.statusCode >= 200 && response.statusCode < 300) {
            saveMiniappUser(response.data)
            resolve(response.data)
            return
          }
          reject(response)
        },
        fail: reject,
      })
    })

  const persist = () => {
    const normalizedPayload = Object.assign({}, payload)
    const avatarPath = normalizedPayload.avatar_url || ""
    if (
      avatarPath &&
      (isTemporaryMiniappFilePath(avatarPath) ||
        (!/^https?:\/\//.test(avatarPath) && !avatarPath.startsWith("/")))
    ) {
      return uploadMiniappAvatar(avatarPath).then((avatarUrl) =>
        send(Object.assign({}, normalizedPayload, { avatar_url: avatarUrl })),
      )
    }
    return send(normalizedPayload)
  }

  if (!getAccessToken()) {
    return ensureMiniappLogin().then(persist)
  }

  return persist()
}

module.exports = {
  ensureMiniappLogin,
  fetchMiniappProfile,
  getAccessToken,
  getMiniappUser,
  clearSession,
  saveMiniappUser,
  updateMiniappProfile,
}
