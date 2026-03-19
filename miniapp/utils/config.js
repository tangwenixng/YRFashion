const defaultConfig = {
  API_ORIGIN: "https://fashion.dadaye.online",
  API_PREFIX: "/api",
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

const config = Object.assign({}, defaultConfig, privateConfig)

config.API_BASE_URL = `${config.API_ORIGIN.replace(/\/$/, "")}${config.API_PREFIX}`

module.exports = config
