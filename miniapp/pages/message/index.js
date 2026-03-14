const { request } = require("../../utils/http")

Page({
  data: {
    productId: null,
    productName: "",
    content: "",
    maxLength: 300,
    submitting: false,
  },

  onLoad(query) {
    const productId = Number(query.productId || 0)
    const productName = query.productName ? decodeURIComponent(query.productName) : "当前商品"
    this.setData({ productId, productName })
  },

  handleInput(event) {
    this.setData({ content: event.detail.value })
  },

  async submitMessage() {
    const content = this.data.content.trim()
    if (!this.data.productId) {
      wx.showToast({ title: "商品信息缺失", icon: "none" })
      return
    }
    if (!content) {
      wx.showToast({ title: "请输入留言内容", icon: "none" })
      return
    }
    if (content.length > this.data.maxLength) {
      wx.showToast({ title: "留言内容过长", icon: "none" })
      return
    }

    this.setData({ submitting: true })
    try {
      await request({
        url: `/miniapp/products/${this.data.productId}/messages`,
        method: "POST",
        data: { content },
        requireAuth: true,
      })
      wx.showToast({ title: "留言已提交", icon: "success" })
      this.setData({ content: "", submitting: false })
      setTimeout(() => {
        wx.navigateBack()
      }, 600)
    } catch (error) {
      this.setData({ submitting: false })
      wx.showToast({ title: "提交失败，请稍后重试", icon: "none" })
    }
  },
})
