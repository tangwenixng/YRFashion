const { ensureConsoleLogin, loginConsole } = require("../utils/console-auth")

Page({
  data: {
    username: "",
    password: "",
    submitting: false,
    error: "",
  },

  onShow() {
    ensureConsoleLogin()
      .then(() => {
        wx.reLaunch({
          url: "/pages-console/home/index",
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
      this.setData({ error: "请输入账号和密码。" })
      wx.showToast({ title: "请先填写登录信息", icon: "none" })
      return
    }

    this.setData({
      submitting: true,
      error: "",
    })

    try {
      await loginConsole(username, password)
      wx.showToast({ title: "登录成功", icon: "success" })
      setTimeout(() => {
        wx.reLaunch({
          url: "/pages-console/home/index",
        })
      }, 300)
    } catch (error) {
      const detail =
        (error && error.data && error.data.detail) ||
        (error && error.detail) ||
        "登录失败。"

      this.setData({
        submitting: false,
        error: detail,
      })
      wx.showToast({ title: "登录失败", icon: "none" })
      return
    }

    this.setData({
      submitting: false,
    })
  },
})
