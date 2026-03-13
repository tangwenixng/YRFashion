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
  username: 'admin',
  password: 'admin123456',
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
      <p class="hero-kicker">Boutique Admin</p>
      <h1>让商品更新、留言处理和店铺运营，都在一个后台里完成。</h1>
      <p class="hero-copy">
        第一版聚焦内容运营，不做复杂电商闭环。先把展示、维护和反馈处理做稳。
      </p>

      <div class="hero-tags">
        <span>Products</span>
        <span>Messages</span>
        <span>Customers</span>
      </div>
    </section>

    <section class="login-card content-card">
      <div class="card-head">
        <p class="card-kicker">YRFasion</p>
        <h2>后台登录</h2>
        <p>使用店主后台账号登录。</p>
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
    radial-gradient(circle at 20% 20%, rgba(242, 179, 109, 0.28), transparent 26%),
    radial-gradient(circle at 82% 16%, rgba(117, 86, 53, 0.2), transparent 18%),
    linear-gradient(145deg, rgba(53, 40, 29, 0.94), rgba(107, 73, 45, 0.9));
  color: #fff8ef;
  box-shadow: 0 28px 80px rgba(61, 39, 21, 0.26);
}

.hero-kicker,
.card-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.hero-kicker {
  color: rgba(255, 236, 211, 0.72);
}

.login-hero h1 {
  max-width: 12ch;
  margin: 18px 0 20px;
  font-family: 'Fraunces', serif;
  font-size: clamp(42px, 6vw, 76px);
  line-height: 0.96;
  letter-spacing: -0.04em;
}

.hero-copy {
  max-width: 520px;
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(255, 244, 230, 0.84);
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.hero-tags span {
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(255, 245, 230, 0.12);
  border: 1px solid rgba(255, 245, 230, 0.14);
}

.login-card {
  align-self: center;
  padding: 32px;
}

.card-head {
  margin-bottom: 24px;
}

.card-kicker {
  color: #9c7657;
}

.card-head h2 {
  margin: 12px 0 8px;
  font-family: 'Fraunces', serif;
  font-size: 34px;
  color: #33261a;
}

.card-head p {
  margin: 0;
  color: #756350;
}

.submit-button {
  width: 100%;
  margin-top: 8px;
  height: 52px;
  border: none;
  background: linear-gradient(135deg, #8f603d, #5f3c24);
}

@media (max-width: 960px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .login-hero,
  .login-card {
    padding: 24px;
  }
}
</style>
