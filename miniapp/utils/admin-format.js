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
    return "Published"
  }
  if (status === "archived") {
    return "Archived"
  }
  return "Draft"
}

function getMessageStatusLabel(status) {
  if (status === "read") {
    return "Read"
  }
  if (status === "replied") {
    return "Replied"
  }
  return "Unread"
}

module.exports = {
  formatDateTime,
  getMessageStatusLabel,
  getProductStatusLabel,
}
