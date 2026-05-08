<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import FortuneForm from "./components/FortuneForm.vue";

const isDark = ref(false);

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
      <p class="eyebrow">Fortune Analysis</p>
      <h1>个性化命理提示词生成器</h1>
      <p>以八字分析为主线，结合星座、MBTI 和当前关注方向，生成可复制的结构化提示词。</p>
      <button data-test="theme-toggle" class="secondary-button" type="button" @click="isDark = !isDark">
        切换到{{ isDark ? "亮色" : "暗色" }}模式
      </button>
    </header>

    <FortuneForm />
  </main>
</template>
