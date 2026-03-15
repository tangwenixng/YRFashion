const { ensureAdminLogin, loginAdmin } = require("../../utils/admin-auth")

Page({
  data: {
    username: "admin",
    password: "",
    submitting: false,
    error: "",
  },

  onShow() {
    ensureAdminLogin()
      .then(() => {
        wx.reLaunch({
          url: "/pages-admin/home/index",
        })
      })
      .catch(() => {})
  },

  handleUsernameInput(event) {
    this.setData({
      username: event.detail.value,
      error: "",
    })
  },

  handlePasswordInput(event) {
    this.setData({
      password: event.detail.value,
      error: "",
    })
  },

  async submit() {
    const username = this.data.username.trim()
    const password = this.data.password

    if (!username || !password) {
      this.setData({ error: "Please enter username and password." })
      wx.showToast({ title: "Missing credentials", icon: "none" })
      return
    }

    this.setData({
      submitting: true,
      error: "",
    })

    try {
      await loginAdmin(username, password)
      wx.showToast({ title: "Login ok", icon: "success" })
      setTimeout(() => {
        wx.reLaunch({
          url: "/pages-admin/home/index",
        })
      }, 300)
    } catch (error) {
      const detail =
        (error && error.data && error.data.detail) ||
        (error && error.detail) ||
        "Login failed."

      this.setData({
        submitting: false,
        error: detail,
      })
      wx.showToast({ title: "Login failed", icon: "none" })
      return
    }

    this.setData({
      submitting: false,
    })
  },
})
