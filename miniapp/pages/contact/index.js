const { request } = require("../../utils/http")

function buildNavigationState(navTitle = "") {
  const systemInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
  const statusBarHeight = Number(systemInfo.statusBarHeight || 20)
  const windowWidth = Number(systemInfo.windowWidth || 375)
  let navBarHeight = 44
  let navRightSpaceWidth = 96

  if (wx.getMenuButtonBoundingClientRect) {
    const menuButtonRect = wx.getMenuButtonBoundingClientRect()
    if (menuButtonRect && menuButtonRect.width) {
      navBarHeight = menuButtonRect.height + (menuButtonRect.top - statusBarHeight) * 2
      navRightSpaceWidth = menuButtonRect.width + (windowWidth - menuButtonRect.right) * 2
    }
  }

  return {
    navTitle,
    statusBarHeight,
    navBarHeight,
    navBarTotalHeight: statusBarHeight + navBarHeight,
    navRightSpaceWidth,
  }
}

const CONSOLE_ENTRY_TAP_THRESHOLD = 10
const CONSOLE_ENTRY_TAP_INTERVAL = 1500

Page({
  data: {
    contact: null,
    loading: true,
    error: "",
  },

  onLoad() {
    this.consoleEntryTapCount = 0
    this.consoleEntryTapTimer = null
    this.setData(buildNavigationState("留言反馈"))
    this.loadContact()
  },

  onUnload() {
    this.resetConsoleEntryTapState()
  },

  async loadContact() {
    this.setData({ loading: true, error: "" })
    try {
      const contact = await request({ url: "/miniapp/shop/contact" })
      this.setData({ contact, loading: false, error: "" })
    } catch (_error) {
      this.setData({ loading: false, error: "联系方式加载失败，请稍后重试。" })
      wx.showToast({ title: "加载失败", icon: "none" })
    }
  },

  goToProducts() {
    wx.navigateTo({ url: "/pages/products/index" })
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" })
  },

  goToMessageHistory() {
    wx.navigateTo({ url: "/pages/message-history/index" })
  },

  goBack() {
    if (getCurrentPages().length > 1) {
      wx.navigateBack({ delta: 1 })
      return
    }
    this.goHome()
  },

  handleConsoleEntryTap() {
    if (this.consoleEntryTapTimer) {
      clearTimeout(this.consoleEntryTapTimer)
    }

    this.consoleEntryTapCount = (this.consoleEntryTapCount || 0) + 1

    if (this.consoleEntryTapCount >= CONSOLE_ENTRY_TAP_THRESHOLD) {
      this.resetConsoleEntryTapState()
      this.goToConsoleLogin()
      return
    }

    this.consoleEntryTapTimer = setTimeout(() => {
      this.resetConsoleEntryTapState()
    }, CONSOLE_ENTRY_TAP_INTERVAL)
  },

  resetConsoleEntryTapState() {
    this.consoleEntryTapCount = 0
    if (this.consoleEntryTapTimer) {
      clearTimeout(this.consoleEntryTapTimer)
      this.consoleEntryTapTimer = null
    }
  },

  goToConsoleLogin() {
    wx.showToast({
      title: "正在进入工作台",
      icon: "none",
      duration: 1200,
    })
    wx.navigateTo({
      url: "/pages-console/login/index",
    })
  },
})
