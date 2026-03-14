const { API_BASE_URL } = require("./config")
const { getAccessToken, clearSession, ensureMiniappLogin } = require("./auth")

function request(options) {
  const {
    url,
    method = "GET",
    data,
    requireAuth = false,
    retryOnAuthFailure = true,
  } = options

  const send = () => {
    const token = getAccessToken()
    const header = Object.assign({}, options.header)
    if (token) {
      header.Authorization = `Bearer ${token}`
    }

    return new Promise((resolve, reject) => {
      wx.request({
        url: `${API_BASE_URL}${url}`,
        method,
        data,
        header,
        success: async (response) => {
          if (response.statusCode === 401 && retryOnAuthFailure) {
            clearSession()
            try {
              await ensureMiniappLogin(true)
              resolve(request(Object.assign({}, options, { retryOnAuthFailure: false })))
            } catch (error) {
              reject(error)
            }
            return
          }

          if (response.statusCode >= 200 && response.statusCode < 300) {
            resolve(response.data)
            return
          }

          reject(response)
        },
        fail: reject,
      })
    })
  }

  if (requireAuth && !getAccessToken()) {
    return ensureMiniappLogin().then(send)
  }

  return send()
}

module.exports = {
  request,
}
