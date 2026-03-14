Page({
  data: {
    userId: null,
  },

  onShow() {
    const app = getApp()
    const user = app.globalData.miniappUser
    this.setData({
      userId: user ? user.id : null,
    })
  },
})
