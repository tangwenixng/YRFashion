export type AdminExperience = 'mobile' | 'desktop'
export type AdminExperienceOverride = 'auto' | 'force-mobile' | 'force-desktop'

export const ADMIN_EXPERIENCE_OVERRIDE_STORAGE_KEY = 'yrfashion-admin-experience-override'
export const mobileAdminNamespace = '/m'

const mobileUserAgentPattern =
  /\b(iPhone|iPod|Android.+Mobile|Mobile Safari|Mobile\/|Windows Phone|webOS|BlackBerry)\b/i

export const isLikelyMobileUserAgent = (userAgent: string) => mobileUserAgentPattern.test(userAgent)

export const resolveAdminExperience = (input: {
  userAgent: string
  override: AdminExperienceOverride
}): AdminExperience => {
  if (input.override === 'force-mobile') {
    return 'mobile'
  }

  if (input.override === 'force-desktop') {
    return 'desktop'
  }

  return isLikelyMobileUserAgent(input.userAgent) ? 'mobile' : 'desktop'
}

export const resolveAdminLoginRoute = (experience: AdminExperience) =>
  experience === 'mobile' ? '/m/login' : '/login'

export const resolveAdminHomeRoute = (experience: AdminExperience) =>
  experience === 'mobile' ? '/m/home' : '/dashboard'
