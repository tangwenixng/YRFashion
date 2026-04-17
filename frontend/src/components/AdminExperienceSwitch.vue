<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  readAdminExperienceOverride,
  resolveAdminExperience,
  resolvePathForExperience,
  writeAdminExperienceOverride,
  type AdminExperienceOverride,
} from '../router/deviceExperience'

const props = withDefaults(
  defineProps<{
    compact?: boolean
  }>(),
  {
    compact: false,
  },
)

const route = useRoute()
const router = useRouter()

const options: Array<{
  label: string
  value: AdminExperienceOverride
}> = [
  { label: '自动', value: 'auto' },
  { label: '手机', value: 'force-mobile' },
  { label: '桌面', value: 'force-desktop' },
]

const currentOverride = computed(() => readAdminExperienceOverride())
const autoExperienceLabel = computed(() => {
  const experience = resolveAdminExperience({
    userAgent: typeof navigator === 'undefined' ? '' : navigator.userAgent,
    override: 'auto',
  })
  return experience === 'mobile' ? '自动=手机' : '自动=桌面'
})

const applyOverride = async (override: AdminExperienceOverride) => {
  writeAdminExperienceOverride(override)

  if (override === 'auto') {
    if (route.path === '/login' || route.path === '/m/login') {
      const autoExperience = resolveAdminExperience({
        userAgent: typeof navigator === 'undefined' ? '' : navigator.userAgent,
        override: 'auto',
      })
      await router.replace(autoExperience === 'mobile' ? '/m/login' : '/login')
    }
    return
  }

  const targetPath = resolvePathForExperience(
    route.fullPath,
    override === 'force-mobile' ? 'mobile' : 'desktop',
  )
  await router.replace(targetPath)
}
</script>

<template>
  <div class="experience-switch" :class="{ compact }">
    <p v-if="!compact" class="switch-caption">体验模式 · {{ autoExperienceLabel }}</p>
    <div class="switch-group">
      <button
        v-for="option in options"
        :key="option.value"
        class="switch-chip"
        :class="{ active: currentOverride === option.value }"
        type="button"
        @click="applyOverride(option.value)"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.experience-switch {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.experience-switch.compact {
  gap: 6px;
}

.switch-caption {
  margin: 0;
  font-size: 12px;
  color: rgba(80, 97, 88, 0.88);
}

.switch-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.switch-chip {
  min-width: 64px;
  height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(57, 76, 64, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  color: #41544a;
  cursor: pointer;
  transition: all 0.18s ease;
}

.switch-chip.active {
  border-color: rgba(47, 106, 88, 0.28);
  background: rgba(47, 106, 88, 0.12);
  color: var(--brand-deep);
}

.switch-chip:hover {
  transform: translateY(-1px);
}

.compact .switch-chip {
  min-width: 56px;
  height: 30px;
  padding: 0 12px;
  font-size: 12px;
}
</style>
