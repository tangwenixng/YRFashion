const { API_BASE_URL } = require("./config")
const { clearAdminSession, getAdminAccessToken, redirectToAdminLogin } = require("./admin-auth")

function request(options) {
  const {
    url,
    method = "GET",
    data,
    header,
  } = options

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data,
      header: Object.assign({}, header, {
        Authorization: `Bearer ${getAdminAccessToken()}`,
      }),
      success: (response) => {
        if (response.statusCode === 401) {
          clearAdminSession()
          redirectToAdminLogin()
          reject(response)
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

function uploadFile(options) {
  const {
    url,
    filePath,
    name = "file",
    formData,
  } = options

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${API_BASE_URL}${url}`,
      filePath,
      name,
      formData,
      header: {
        Authorization: `Bearer ${getAdminAccessToken()}`,
      },
      success: (response) => {
        let payload = {}
        try {
          payload = JSON.parse(response.data || "{}")
        } catch (_error) {
          reject(new Error("Failed to parse upload response"))
          return
        }

        if (response.statusCode === 401) {
          clearAdminSession()
          redirectToAdminLogin()
          reject(payload)
          return
        }

        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(payload)
          return
        }

        reject(payload)
      },
      fail: reject,
    })
  })
}

module.exports = {
  request,
  uploadFile,
}
