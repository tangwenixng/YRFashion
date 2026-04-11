const UNKNOWN_BUILD_TIME = '未知版本'

const pad = (value: number) => String(value).padStart(2, '0')

export const resolveBuildTimeLabel = (buildTime = import.meta.env.VITE_APP_BUILD_TIME) => {
  const normalizedBuildTime = buildTime?.trim()
  if (!normalizedBuildTime || normalizedBuildTime === 'unknown') {
    return UNKNOWN_BUILD_TIME
  }

  const timestamp = Date.parse(normalizedBuildTime)
  if (Number.isNaN(timestamp)) {
    return normalizedBuildTime
  }

  const date = new Date(timestamp)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
