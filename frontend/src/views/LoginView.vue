<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AdminExperienceSwitch from '../components/AdminExperienceSwitch.vue'
import { useAuthStore } from '../stores/auth'
import {
  readAdminExperienceOverride,
  resolveAdminHomeRoute,
  resolveExperienceForPath,
  sanitizeRedirectTarget,
} from '../router/deviceExperience'

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
    ? '适合 Android Chrome / iPhone Safari 的轻量运营入口。'
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
      <div class="hero-brand">
        <span class="hero-brand-mark">YR</span>
        <div>
          <p class="hero-kicker">YRFashion Admin</p>
          <strong>{{ isMobileExperience ? 'Mobile Console' : 'Desktop Console' }}</strong>
        </div>
      </div>

      <div class="hero-copy-block">
        <h1>{{ isMobileExperience ? '手机小屏后台' : 'SzYR OOTD' }}</h1>
        <p class="hero-copy">
          {{
            isMobileExperience
              ? '更适合在手机浏览器中快速处理留言、商品与图片，不再勉强压缩桌面后台。'
              : '桌面版继续保留完整信息密度，适合长时间编辑与运营。'
          }}
        </p>
      </div>

      <AdminExperienceSwitch />
    </section>

    <section class="login-card content-card">
      <div class="card-head">
        <p class="card-kicker">{{ isMobileExperience ? 'Mobile Admin' : 'YRFashion' }}</p>
        <h2>{{ loginTitle }}</h2>
        <p>{{ loginSubtitle }}</p>
      </div>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" size="large" placeholder="请输入用户名">
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

      <p class="login-footnote">
        <a href="https://beian.miit.gov.cn/#/Integrated/index">苏ICP备19033375号-2</a>
      </p>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  grid-template-columns: 1.12fr 0.88fr;
  padding: 28px;
  gap: 24px;
}

.login-page.mobile {
  grid-template-columns: 1fr;
  max-width: 560px;
  margin: 0 auto;
  padding: 18px 16px 28px;
  gap: 16px;
}

.login-hero,
.login-card {
  min-width: 0;
}

.login-hero {
  padding: 48px;
  border-radius: 34px;
  background:
    radial-gradient(circle at 18% 18%, rgba(192, 138, 54, 0.18), transparent 24%),
    radial-gradient(circle at 82% 16%, rgba(47, 106, 88, 0.16), transparent 24%),
    linear-gradient(145deg, rgba(29, 67, 56, 0.96), rgba(53, 96, 81, 0.92));
  color: #f7f8f4;
  box-shadow: 0 28px 80px rgba(27, 49, 41, 0.26);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 24px;
}

.login-page.mobile .login-hero {
  padding: 24px 22px;
  border-radius: 28px;
  gap: 18px;
}

.hero-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-brand-mark {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #f8fbf7;
  font-family: 'Sora', sans-serif;
  font-size: 22px;
  font-weight: 700;
}

.hero-brand strong {
  display: block;
  margin-top: 6px;
  color: rgba(247, 248, 244, 0.96);
  font-size: 18px;
  font-weight: 700;
}

.hero-kicker,
.card-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.hero-kicker {
  color: rgba(236, 244, 239, 0.68);
}

.hero-copy-block {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.login-hero h1 {
  max-width: 12ch;
  margin: 0;
  font-family: 'Sora', sans-serif;
  font-size: clamp(40px, 5.6vw, 68px);
  line-height: 1.02;
  letter-spacing: -0.05em;
}

.login-page.mobile .login-hero h1 {
  max-width: none;
  font-size: clamp(28px, 9vw, 42px);
  line-height: 1.08;
}

.hero-copy {
  max-width: 560px;
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(234, 243, 237, 0.84);
}

.login-page.mobile .hero-copy {
  font-size: 15px;
  line-height: 1.7;
}

.login-card {
  align-self: center;
  width: 100%;
  padding: 36px 34px;
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.1), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(255, 255, 255, 0.34)),
    var(--bg-panel);
}

.login-page.mobile .login-card {
  padding: 24px 20px;
  border-radius: 24px;
}

.card-head {
  margin-bottom: 24px;
}

.card-kicker {
  color: var(--brand);
}

.card-head h2 {
  margin: 12px 0 8px;
  font-family: 'Sora', sans-serif;
  font-size: 34px;
  color: var(--ink-strong);
}

.login-page.mobile .card-head h2 {
  font-size: 28px;
}

.card-head p,
.login-footnote {
  margin: 0;
  color: var(--ink-soft);
}

.login-card :deep(.el-form-item__label) {
  color: #506158;
  font-weight: 600;
}

.login-card :deep(.el-input__wrapper) {
  min-height: 52px;
  border-radius: 16px;
  box-shadow: inset 0 0 0 1px rgba(57, 76, 64, 0.12);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px rgba(47, 106, 88, 0.48),
    0 0 0 4px rgba(47, 106, 88, 0.08);
}

.submit-button {
  width: 100%;
  margin-top: 12px;
  height: 52px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(145deg, var(--brand), var(--brand-deep));
  box-shadow: 0 14px 28px rgba(29, 67, 56, 0.22);
}

.submit-button:hover,
.submit-button:focus {
  background: linear-gradient(145deg, #377865, #244e42);
}

.login-footnote {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
}

@media (max-width: 1180px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 18px;
    gap: 18px;
  }

  .login-hero {
    padding: 22px 24px;
    border-radius: 28px;
  }

  .login-hero h1 {
    max-width: none;
    font-size: clamp(28px, 4.6vw, 42px);
    line-height: 1.08;
  }

  .hero-brand-mark {
    width: 50px;
    height: 50px;
    border-radius: 18px;
    font-size: 20px;
  }

  .login-card {
    padding: 28px 24px;
  }
}
</style>
