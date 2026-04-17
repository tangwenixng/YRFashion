<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AdminExperienceSwitch from '../components/AdminExperienceSwitch.vue'
import {
  readAdminExperienceOverride,
  resolveAdminHomeRoute,
  resolveExperienceForPath,
  sanitizeRedirectTarget,
} from '../router/deviceExperience'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const isMobileExperience = computed(() => route.path.startsWith('/m/'))
const loginTitle = computed(() => (isMobileExperience.value ? '手机后台登录' : '登录'))
const loginSubtitle = computed(() =>
  isMobileExperience.value
    ? '适合 Android Chrome / iPhone Safari 的单手操作节奏。'
    : '继续使用当前桌面版管理后台。',
)

const submit = async () => {
  if (loading.value) {
    return
  }

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    const redirectTarget = sanitizeRedirectTarget(
      typeof route.query.redirect === 'string' ? route.query.redirect : undefined,
    )
    const fallbackExperience = resolveExperienceForPath({
      path: route.path,
      userAgent: typeof navigator === 'undefined' ? '' : navigator.userAgent,
      override: readAdminExperienceOverride(),
    })
    ElMessage.success(isMobileExperience.value ? '已进入手机后台' : '已进入管理后台')
    await router.push(redirectTarget || resolveAdminHomeRoute(fallbackExperience))
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page" :class="{ mobile: isMobileExperience }">
    <section class="login-hero">
      <div class="hero-brand-row">
        <div class="hero-brand-lockup">
          <span class="hero-brand-mark">YR</span>
          <div>
            <p class="hero-kicker">YRFashion Admin</p>
            <strong>{{ isMobileExperience ? 'Mobile Atelier' : 'Desktop Console' }}</strong>
          </div>
        </div>
        <AdminExperienceSwitch compact light />
      </div>

      <div class="hero-copy-block">
        <span class="mobile-overline hero-overline">Fashion Ops</span>
        <h1>{{ isMobileExperience ? '手机小屏后台' : 'SzYR OOTD' }}</h1>
        <p class="hero-copy">
          {{
            isMobileExperience
              ? '留言、商品、图片处理重新按手机节奏排布：更清晰、更好点按。'
              : '桌面版继续保留完整信息密度，适合长时间编辑、运营与后台配置。'
          }}
        </p>
      </div>

      <div class="hero-bullet-row">
        <span class="hero-mini-card">单手更顺</span>
        <span class="hero-mini-card">桌面保留</span>
      </div>
    </section>

    <section class="login-card content-card">
      <div class="card-head">
        <p class="card-kicker">{{ isMobileExperience ? 'Mobile Admin' : 'YRFashion' }}</p>
        <h2>{{ loginTitle }}</h2>
        <p>{{ loginSubtitle }}</p>
      </div>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" size="large" placeholder="请输入用户名" inputmode="text">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            show-password
            placeholder="请输入密码"
            inputmode="text"
            @keyup.enter="submit"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-button class="submit-button" size="large" type="primary" :loading="loading" @click="submit">
          {{ isMobileExperience ? '登录并进入手机后台' : '登录并进入后台' }}
        </el-button>
      </el-form>

      <div class="login-note-row">
        <span>默认管理员：admin / admin123456</span>
        <a href="https://beian.miit.gov.cn/#/Integrated/index">苏ICP备19033375号-2</a>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  padding: 28px;
  gap: 24px;
}

.login-page.mobile {
  grid-template-columns: 1fr;
  max-width: 560px;
  margin: 0 auto;
  padding: 16px 16px 28px;
  gap: 14px;
}

.login-hero,
.login-card {
  min-width: 0;
}

.login-hero {
  padding: 24px;
  border-radius: 34px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.08), transparent 24%),
    linear-gradient(155deg, var(--mobile-shell-dark), var(--mobile-shell-deep));
  color: #f8f3ec;
  box-shadow: 0 28px 70px rgba(26, 37, 33, 0.24);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-brand-row {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-brand-lockup {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-brand-mark {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #f8fbf7;
  font-family: 'Sora', sans-serif;
  font-size: 22px;
  font-weight: 700;
}

.hero-kicker,
.card-kicker {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.26em;
  text-transform: uppercase;
}

.hero-kicker {
  color: rgba(236, 244, 239, 0.62);
}

.hero-brand-lockup strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
}

.hero-copy-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-overline {
  width: fit-content;
}

.login-hero h1 {
  margin: 0;
  font-family: 'Playfair Display', serif;
  font-size: clamp(38px, 10vw, 58px);
  line-height: 0.95;
  letter-spacing: -0.05em;
}

.login-page.mobile .login-hero h1 {
  font-size: clamp(30px, 10vw, 42px);
}

.hero-copy {
  margin: 0;
  font-size: 15px;
  line-height: 1.72;
  color: rgba(234, 243, 237, 0.82);
}

.hero-bullet-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.hero-mini-card {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(247, 243, 236, 0.82);
  font-size: 13px;
  font-weight: 700;
}

.login-card {
  align-self: center;
  width: 100%;
  padding: 26px 22px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.4)),
    var(--bg-panel);
}

.login-page.mobile .login-card {
  padding: 22px 18px;
  border-radius: 26px;
}

.card-head {
  margin-bottom: 18px;
}

.card-kicker {
  color: var(--accent-gold);
}

.card-head h2 {
  margin: 12px 0 8px;
  font-family: 'Playfair Display', serif;
  font-size: 34px;
  letter-spacing: -0.03em;
  color: #1f241f;
}

.card-head p,
.login-note-row {
  margin: 0;
  color: var(--ink-soft);
}

.login-card :deep(.el-form-item) {
  margin-bottom: 16px;
}

.login-card :deep(.el-form-item__label) {
  color: #506158;
  font-weight: 600;
}

.login-card :deep(.el-input__wrapper) {
  min-height: 54px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: inset 0 0 0 1px rgba(57, 76, 64, 0.08);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px rgba(47, 106, 88, 0.42),
    0 0 0 4px rgba(47, 106, 88, 0.08);
}

.submit-button {
  width: 100%;
  margin-top: 6px;
  height: 54px;
  border: none;
  border-radius: 20px;
  background: linear-gradient(145deg, var(--brand), var(--brand-deep));
  box-shadow: 0 16px 30px rgba(29, 67, 56, 0.2);
}

.login-note-row {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

@media (max-width: 1180px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 18px;
    gap: 18px;
  }

  .login-hero {
    border-radius: 30px;
  }
}
</style>
