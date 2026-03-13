<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <main class="placeholder-page">
    <section class="placeholder-card">
      <p class="eyebrow">YRFasion Admin</p>
      <h1>{{ (route.meta.section as string) || '管理后台' }}</h1>
      <p class="description">
        当前页面骨架已创建。接下来会按功能逐步接入登录、数据请求和实际交互。
      </p>
      <div class="path-chip">{{ route.path }}</div>
    </section>
  </main>
</template>

<style scoped>
.placeholder-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(239, 164, 107, 0.22), transparent 30%),
    linear-gradient(135deg, #f6f1e8 0%, #f2ebe0 45%, #ebe2d2 100%);
}

.placeholder-card {
  width: min(640px, 100%);
  padding: 40px;
  border-radius: 28px;
  background: rgba(255, 252, 247, 0.9);
  border: 1px solid rgba(126, 91, 58, 0.14);
  box-shadow: 0 20px 60px rgba(92, 62, 36, 0.12);
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #8d6a4a;
}

h1 {
  margin: 0;
  font-size: clamp(32px, 5vw, 52px);
  line-height: 1;
  color: #2d241b;
}

.description {
  margin: 16px 0 0;
  font-size: 16px;
  line-height: 1.7;
  color: #5a4c3e;
}

.path-chip {
  display: inline-flex;
  margin-top: 24px;
  padding: 10px 14px;
  border-radius: 999px;
  background: #2d241b;
  color: #fff7ed;
  font-size: 13px;
}
</style>
