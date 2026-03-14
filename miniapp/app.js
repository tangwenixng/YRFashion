const { ensureMiniappLogin } = require("./utils/auth")

App({
  globalData: {
    miniappUser: null,
  },

  onLaunch() {
    ensureMiniappLogin()
      .then((session) => {
        this.globalData.miniappUser = session.user
      })
      .catch(() => {
        // Public pages can still render without a session; protected actions retry login.
      })
  },
})
