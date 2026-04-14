const defaultEnvConfigMap = {
  develop: {
    API_ORIGIN: "https://today.dcove.cn",
    API_PREFIX: "/fashion/api",
  },
  trial: {
    API_ORIGIN: "https://today.dcove.cn",
    API_PREFIX: "/fashion/api",
  },
  release: {
    API_ORIGIN: "https://fashion.dadaye.online",
    API_PREFIX: "/api",
  },
}

const defaultConfig = {
  TOKEN_STORAGE_KEY: "yrfasion-miniapp-token",
  USER_STORAGE_KEY: "yrfasion-miniapp-user",
  CONSOLE_TOKEN_STORAGE_KEY: "yrfasion-console-token",
  CONSOLE_PROFILE_STORAGE_KEY: "yrfasion-console-profile",
}

let privateConfig = {}

try {
  privateConfig = require("./config.private")
} catch (error) {
  privateConfig = {}
}

function resolveMiniProgramEnvVersion() {
  try {
    if (typeof wx === "undefined" || typeof wx.getAccountInfoSync !== "function") {
      return "release"
    }

    const accountInfo = wx.getAccountInfoSync()
    const envVersion = accountInfo && accountInfo.miniProgram && accountInfo.miniProgram.envVersion
    return envVersion || "release"
  } catch (error) {
    return "release"
  }
}

const envVersion = resolveMiniProgramEnvVersion()
const privateEnvConfigMap =
  privateConfig && typeof privateConfig.ENV_CONFIG === "object" && privateConfig.ENV_CONFIG
    ? privateConfig.ENV_CONFIG
    : {}

const envConfig = Object.assign(
  {},
  defaultEnvConfigMap.release,
  defaultEnvConfigMap[envVersion] || {},
  privateEnvConfigMap[envVersion] || {},
)

const legacyOverrideConfig = {}
if (typeof privateConfig.API_ORIGIN === "string") {
  legacyOverrideConfig.API_ORIGIN = privateConfig.API_ORIGIN
}
if (typeof privateConfig.API_PREFIX === "string") {
  legacyOverrideConfig.API_PREFIX = privateConfig.API_PREFIX
}

const config = Object.assign({}, defaultConfig, envConfig, privateConfig, legacyOverrideConfig)

config.API_BASE_URL = `${config.API_ORIGIN.replace(/\/$/, "")}${config.API_PREFIX}`
config.MINI_PROGRAM_ENV_VERSION = envVersion

module.exports = config
