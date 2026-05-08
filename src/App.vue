<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import FortuneForm from "./components/FortuneForm.vue";

const isDark = ref(false);
const currentYear = new Date().getFullYear();

watch(
  isDark,
  (value) => {
    document.documentElement.dataset.theme = value ? "dark" : "light";
  },
  { immediate: true },
);

onMounted(() => {
  document.documentElement.dataset.theme = isDark.value ? "dark" : "light";
});
</script>

<template>
  <main class="app-shell" :class="{ dark: isDark }">
    <header class="app-header">
      <p class="eyebrow">八字为纲 · 星座与性格加持</p>
      <h1>一键生成可复制的命理提示词</h1>
      <p class="app-lead">
        以八字分析为主线,结合星座、MBTI 和当前关注方向,为你生成可一键复制的结构化提示词。
      </p>
      <button
        data-test="theme-toggle"
        class="theme-icon-button header-corner-button"
        type="button"
        aria-label="切换暗黑模式"
        @click="isDark = !isDark"
      >
        ☀
      </button>
    </header>

    <FortuneForm />

    <footer class="app-footer">
      <p>© {{ currentYear }} Fortune Analysis · 仅供学习与交流使用，不构成任何决策或医疗建议。</p>
    </footer>
  </main>
</template>
