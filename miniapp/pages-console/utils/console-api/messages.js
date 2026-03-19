const { request } = require("../console-http")
const { normalizeMediaUrl } = require("../../../utils/media")

function normalizeMessage(message) {
  if (!message) {
    return message
  }

  return Object.assign({}, message, {
    miniapp_user_avatar_url: normalizeMediaUrl(message.miniapp_user_avatar_url),
  })
}

function fetchConsoleMessages(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ""
  return request({
    url: `/admin/messages${query}`,
  }).then((response) => (response.items || []).map(normalizeMessage))
}

function markConsoleMessageRead(messageId) {
  return request({
    url: `/admin/messages/${messageId}/read`,
    method: "POST",
  }).then(normalizeMessage)
}

function markConsoleMessageUnread(messageId) {
  return request({
    url: `/admin/messages/${messageId}/unread`,
    method: "POST",
  }).then(normalizeMessage)
}

function replyConsoleMessage(messageId, replyContent) {
  return request({
    url: `/admin/messages/${messageId}/reply`,
    method: "POST",
    data: {
      reply_content: replyContent,
    },
  }).then(normalizeMessage)
}

module.exports = {
  fetchConsoleMessages,
  markConsoleMessageRead,
  markConsoleMessageUnread,
  replyConsoleMessage,
}
