const { API_BASE_URL } = require("../../utils/config")
const { clearConsoleSession, getConsoleAccessToken, redirectToConsoleLogin } = require("./console-auth")

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
        Authorization: `Bearer ${getConsoleAccessToken()}`,
      }),
      success: (response) => {
        if (response.statusCode === 401) {
          clearConsoleSession()
          redirectToConsoleLogin()
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
        Authorization: `Bearer ${getConsoleAccessToken()}`,
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
          clearConsoleSession()
          redirectToConsoleLogin()
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
