const { request } = require("../admin-http")
const { normalizeMediaUrl } = require("../media")

function normalizeMessage(message) {
  if (!message) {
    return message
  }

  return Object.assign({}, message, {
    miniapp_user_avatar_url: normalizeMediaUrl(message.miniapp_user_avatar_url),
  })
}

function fetchAdminMessages(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ""
  return request({
    url: `/admin/messages${query}`,
  }).then((response) => (response.items || []).map(normalizeMessage))
}

function markAdminMessageRead(messageId) {
  return request({
    url: `/admin/messages/${messageId}/read`,
    method: "POST",
  }).then(normalizeMessage)
}

function markAdminMessageUnread(messageId) {
  return request({
    url: `/admin/messages/${messageId}/unread`,
    method: "POST",
  }).then(normalizeMessage)
}

function replyAdminMessage(messageId, replyContent) {
  return request({
    url: `/admin/messages/${messageId}/reply`,
    method: "POST",
    data: {
      reply_content: replyContent,
    },
  }).then(normalizeMessage)
}

module.exports = {
  fetchAdminMessages,
  markAdminMessageRead,
  markAdminMessageUnread,
  replyAdminMessage,
}
