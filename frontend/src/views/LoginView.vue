<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const submit = async () => {
  if (loading.value) {
    return
  }

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('已进入管理后台')
    await router.push('/dashboard')
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-hero">
      <div class="hero-brand">
        <span class="hero-brand-mark">YR</span>
        <div>
          <p class="hero-kicker">YRFashion Admin</p>
          <strong>商品管理后台</strong>
        </div>
      </div>
      <h1>伊人时尚</h1>
      <p class="hero-copy">
        苏州市高新区何山路176号。
      </p>
    </section>

    <section class="login-card content-card">
      <div class="card-head">
        <p class="card-kicker">YRFashion</p>
        <h2>后台登录</h2>
        <p>使用店铺后台账号进入商品运营台。</p>
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
          登录并进入后台
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  padding: 28px;
  gap: 24px;
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

.login-hero h1 {
  max-width: 12ch;
  margin: 28px 0 20px;
  font-family: 'Sora', sans-serif;
  font-size: clamp(40px, 5.6vw, 68px);
  line-height: 1.02;
  letter-spacing: -0.05em;
}

.hero-copy {
  max-width: 560px;
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(234, 243, 237, 0.84);
}

.login-card {
  align-self: center;
  padding: 36px 34px;
  background:
    radial-gradient(circle at top right, rgba(192, 138, 54, 0.1), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(255, 255, 255, 0.34)),
    var(--bg-panel);
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

.card-head p {
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
    margin: 16px 0 10px;
    font-size: clamp(28px, 4.6vw, 42px);
    line-height: 1.08;
  }

  .hero-brand-mark {
    width: 50px;
    height: 50px;
    border-radius: 18px;
    font-size: 20px;
  }

  .hero-brand strong {
    font-size: 16px;
  }

  .hero-copy {
    max-width: none;
    font-size: 15px;
    line-height: 1.65;
  }

  .login-card {
    padding: 28px 24px;
  }
}

@media (max-width: 767px) {
  .login-page {
    padding: 16px;
  }

  .login-hero,
  .login-card {
    padding: 24px;
  }

  .login-hero h1 {
    font-size: clamp(34px, 11vw, 48px);
  }
}
</style>
