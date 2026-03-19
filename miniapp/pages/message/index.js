const { fetchMiniappProfile, getMiniappUser, updateMiniappProfile } = require("../../utils/auth")
const { request } = require("../../utils/http")
const { normalizeMediaUrl } = require("../../utils/media")

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

function buildProfileState(user) {
  const nickname = (user && user.nickname) || ""
  const avatarUrl = (user && (user.pending_avatar_url || user.avatar_url)) || ""
  const displayAvatarUrl = avatarUrl ? normalizeMediaUrl(avatarUrl) : ""
  const avatarReviewStatus = (user && user.avatar_review_status) || "approved"
  const avatarRejectReason = (user && user.avatar_reject_reason) || ""

  return {
    profileNickname: nickname,
    profileAvatarUrl: displayAvatarUrl,
    savedProfileNickname: nickname,
    savedProfileAvatarUrl: displayAvatarUrl,
    needsProfileCompletion: !nickname || !avatarUrl,
    avatarReviewStatus,
    avatarRejectReason,
  }
}

function resolveErrorMessage(error, fallback) {
  if (error && error.data && typeof error.data.detail === "string" && error.data.detail.trim()) {
    return error.data.detail
  }

  if (error && typeof error.detail === "string" && error.detail.trim()) {
    return error.detail
  }

  return fallback
}

Page({
  data: {
    productId: null,
    productName: "",
    content: "",
    maxLength: 300,
    submitting: false,
    profileNickname: "",
    profileAvatarUrl: "",
    savedProfileNickname: "",
    savedProfileAvatarUrl: "",
    needsProfileCompletion: true,
    nicknameFocused: false,
    avatarReviewStatus: "approved",
    avatarRejectReason: "",
  },

  onLoad(query) {
    const productId = Number(query.productId || 0)
    const productName = query.productName ? decodeURIComponent(query.productName) : "当前穿搭"
    this.setData(
      Object.assign(
        {
          productId,
          productName,
          ...buildNavigationState(productName || "留言交流"),
        },
        buildProfileState(getMiniappUser()),
      ),
    )
    this.syncProfile()
  },

  async syncProfile() {
    try {
      const profile = await fetchMiniappProfile()
      this.setData(buildProfileState(profile))
    } catch (_error) {
      // Keep local cached profile as a fallback when the network is unavailable.
    }
  },

  handleInput(event) {
    this.setData({ content: event.detail.value })
  },

  handleNicknameInput(event) {
    this.setData({ profileNickname: event.detail.value })
  },

  handleNicknameFocus() {
    this.setData({ nicknameFocused: true })
  },

  handleNicknameBlur() {
    this.setData({ nicknameFocused: false })
  },

  handleChooseAvatar(event) {
    const avatarUrl = event.detail.avatarUrl || ""
    this.setData({
      profileAvatarUrl: avatarUrl,
      needsProfileCompletion: !this.data.profileNickname.trim() || !avatarUrl,
      avatarReviewStatus: "pending",
      avatarRejectReason: "",
    })
  },

  async ensureProfileReady() {
    const nickname = this.data.profileNickname.trim()
    const avatarUrl = this.data.profileAvatarUrl

    if (!nickname) {
      wx.showToast({ title: "请先填写昵称", icon: "none" })
      return false
    }

    if (!avatarUrl) {
      wx.showToast({ title: "请先选择头像", icon: "none" })
      return false
    }

    const hasChanges =
      nickname !== this.data.savedProfileNickname || avatarUrl !== this.data.savedProfileAvatarUrl

    if (!hasChanges && !this.data.needsProfileCompletion) {
      return true
    }

    const profile = await updateMiniappProfile({
      nickname,
      avatar_url: avatarUrl,
    })
    const finalAvatarUrl = profile.pending_avatar_url || profile.avatar_url || avatarUrl
    const normalizedAvatarUrl = finalAvatarUrl ? normalizeMediaUrl(finalAvatarUrl) : ""

    this.setData({
      profileNickname: profile.nickname || nickname,
      profileAvatarUrl: normalizedAvatarUrl,
      savedProfileNickname: profile.nickname || nickname,
      savedProfileAvatarUrl: normalizedAvatarUrl,
      needsProfileCompletion: false,
      avatarReviewStatus: profile.avatar_review_status || "approved",
      avatarRejectReason: profile.avatar_reject_reason || "",
    })
    return true
  },

  async submitMessage() {
    const content = this.data.content.trim()
    if (!this.data.productId) {
      wx.showToast({ title: "穿搭信息缺失", icon: "none" })
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
      const ready = await this.ensureProfileReady()
      if (!ready) {
        this.setData({ submitting: false })
        return
      }

      await request({
        url: `/miniapp/products/${this.data.productId}/messages`,
        method: "POST",
        data: { content },
        requireAuth: true,
      })
      wx.showToast({ title: "留言已提交", icon: "success" })
      this.setData({ content: "", submitting: false })
      setTimeout(() => {
        const productName = encodeURIComponent(this.data.productName || "")
        wx.redirectTo({
          url: `/pages/message-history/index?productId=${this.data.productId}&productName=${productName}`,
        })
      }, 600)
    } catch (error) {
      this.setData({ submitting: false })
      wx.showToast({
        title: resolveErrorMessage(error, "提交失败，请稍后重试"),
        icon: "none",
      })
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" })
  },

  goBack() {
    if (getCurrentPages().length > 1) {
      wx.navigateBack({ delta: 1 })
      return
    }
    this.goHome()
  },
})
