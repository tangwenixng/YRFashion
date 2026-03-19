function pad(value) {
  return String(value).padStart(2, "0")
}

function formatDateTime(value) {
  if (!value) {
    return ""
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function getProductStatusLabel(status) {
  if (status === "published") {
    return "已发布"
  }
  if (status === "archived") {
    return "已归档"
  }
  return "草稿"
}

function getMessageStatusLabel(status) {
  if (status === "read") {
    return "已读"
  }
  if (status === "replied") {
    return "已回复"
  }
  return "未读"
}

module.exports = {
  formatDateTime,
  getMessageStatusLabel,
  getProductStatusLabel,
}
