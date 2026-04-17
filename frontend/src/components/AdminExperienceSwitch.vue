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
    light?: boolean
  }>(),
  {
    compact: false,
    light: false,
  },
)

const route = useRoute()
const router = useRouter()

const options: Array<{ label: string; value: AdminExperienceOverride }> = [
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
  return experience === 'mobile' ? '自动识别为手机' : '自动识别为桌面'
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
  <div class="experience-switch" :class="{ compact, light }">
    <p v-if="!compact" class="switch-caption">{{ autoExperienceLabel }}</p>
    <div class="switch-group" role="tablist" aria-label="体验模式切换">
      <button
        v-for="option in options"
        :key="option.value"
        class="switch-chip"
        :class="{ active: currentOverride === option.value }"
        type="button"
        :aria-pressed="currentOverride === option.value"
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
  gap: 10px;
}

.experience-switch.compact {
  gap: 6px;
}

.switch-caption {
  margin: 0;
  font-size: 12px;
  color: rgba(248, 244, 236, 0.72);
}

.light .switch-caption {
  color: rgba(86, 95, 89, 0.9);
}

.switch-group {
  display: inline-grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
}

.light .switch-group {
  background: rgba(34, 48, 42, 0.08);
  border-color: rgba(34, 48, 42, 0.08);
}

.switch-chip {
  min-height: 40px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(248, 244, 236, 0.88);
  font-size: 13px;
  font-weight: 600;
  transition:
    background 180ms ease,
    color 180ms ease,
    transform 180ms ease,
    box-shadow 180ms ease;
}

.light .switch-chip {
  color: #526058;
}

.switch-chip.active {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(244, 237, 228, 0.98));
  color: #1f2925;
  box-shadow: 0 8px 18px rgba(18, 25, 22, 0.12);
}

.switch-chip:hover,
.switch-chip:focus-visible {
  transform: translateY(-1px);
}

.compact .switch-chip {
  min-height: 34px;
  font-size: 12px;
}
</style>
