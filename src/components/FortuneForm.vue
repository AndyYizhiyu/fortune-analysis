<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import {
  fetchHistory,
  fetchHistoryDetail,
  optimizePrompt,
  type HistoryDetail,
  type HistoryListItem,
  type OptimizePayload,
} from "../lib/api";
import { calculateZodiac, zodiacOptions } from "../lib/zodiac";

const elementOptions = ["金", "木", "水", "火", "土"];
const mbtiOptions = [
  "不知道/暂不填写",
  "ISTJ",
  "ISFJ",
  "INFJ",
  "INTJ",
  "ISTP",
  "ISFP",
  "INFP",
  "INTP",
  "ESTP",
  "ESFP",
  "ENFP",
  "ENTP",
  "ESTJ",
  "ESFJ",
  "ENFJ",
  "ENTJ",
];
const focusOptions = ["工作", "感情", "财运", "学业", "考试", "健康", "人际", "家庭"];
const provinceOptions = [
  "北京市",
  "天津市",
  "上海市",
  "重庆市",
  "河北省",
  "山西省",
  "辽宁省",
  "吉林省",
  "黑龙江省",
  "江苏省",
  "浙江省",
  "安徽省",
  "福建省",
  "江西省",
  "山东省",
  "河南省",
  "湖北省",
  "湖南省",
  "广东省",
  "海南省",
  "四川省",
  "贵州省",
  "云南省",
  "陕西省",
  "甘肃省",
  "青海省",
  "台湾省",
  "内蒙古自治区",
  "广西壮族自治区",
  "西藏自治区",
  "宁夏回族自治区",
  "新疆维吾尔自治区",
  "香港特别行政区",
  "澳门特别行政区",
];
const today = new Date();
const currentYear = today.getFullYear();
const yearOptions = Array.from({ length: currentYear - 1945 + 1 }, (_, index) => String(currentYear - index));
const monthOptions = Array.from({ length: 12 }, (_, index) => String(index + 1));

const form = reactive({
  birthYear: "",
  birthMonth: "",
  birthDay: "",
  birthTime: "",
  province: "",
  city: "",
  district: "",
  gender: "不便透露",
  fiveElements: [] as string[],
  zodiac: "",
  mbti: "不知道/暂不填写",
  focusAreas: [] as string[],
});

const prompt = ref("");
const error = ref("");
const loading = ref(false);
const copied = ref(false);
const historyItems = ref<HistoryListItem[]>([]);
const selectedHistory = ref<HistoryDetail | null>(null);

const birthDate = computed(() => {
  if (!form.birthYear || !form.birthMonth || !form.birthDay) {
    return "";
  }

  return `${form.birthYear}-${padDatePart(form.birthMonth)}-${padDatePart(form.birthDay)}`;
});

const dayOptions = computed(() => {
  if (!form.birthYear || !form.birthMonth) {
    return Array.from({ length: 31 }, (_, index) => String(index + 1));
  }

  const daysInMonth = new Date(Number(form.birthYear), Number(form.birthMonth), 0).getDate();
  return Array.from({ length: daysInMonth }, (_, index) => String(index + 1));
});

watch(
  birthDate,
  (value) => {
    form.zodiac = calculateZodiac(value);
  },
);

watch(dayOptions, (options) => {
  if (form.birthDay && !options.includes(String(form.birthDay))) {
    form.birthDay = "";
  }
});

onMounted(async () => {
  try {
    historyItems.value = await fetchHistory();
  } catch {
    historyItems.value = [];
  }
});

async function submitForm() {
  error.value = "";
  prompt.value = "";
  copied.value = false;

  const validationError = validateForm();
  if (validationError) {
    error.value = validationError;
    return;
  }

  try {
    loading.value = true;
    const result = await optimizePrompt(toPayload());
    prompt.value = result.optimizedPrompt;
    selectedHistory.value = null;
    historyItems.value = [
      {
        id: result.id,
        createdAt: result.createdAt,
        preview: Array.from(result.optimizedPrompt).slice(0, 50).join(""),
      },
      ...historyItems.value,
    ].slice(0, 10);
  } catch (unknownError) {
    error.value = unknownError instanceof Error ? unknownError.message : "提示词生成失败";
  } finally {
    loading.value = false;
  }
}

async function copyPrompt() {
  if (!prompt.value) {
    return;
  }

  await navigator.clipboard.writeText(prompt.value);
  copied.value = true;
}

function toPayload(): OptimizePayload {
  return {
    birthDate: birthDate.value,
    birthTime: form.birthTime || null,
    birthPlace: {
      province: form.province,
      city: form.city || null,
      district: form.district || null,
    },
    gender: form.gender,
    fiveElements: form.fiveElements,
    zodiac: form.zodiac || null,
    mbti: form.mbti,
    focusAreas: form.focusAreas,
  };
}

function padDatePart(value: string): string {
  return String(value).padStart(2, "0");
}

async function showHistoryDetail(id: string) {
  selectedHistory.value = await fetchHistoryDetail(id);
}

function validateForm(): string {
  if (!birthDate.value || !isRealDate(birthDate.value)) {
    return "请选择正确的出生年月日";
  }

  if (new Date(`${birthDate.value}T00:00:00`) > startOfToday()) {
    return "出生日期不能晚于今天";
  }

  return "";
}

function isRealDate(value: string): boolean {
  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(`${value}T00:00:00`);
  return (
    !Number.isNaN(parsed.getTime()) &&
    parsed.getFullYear() === year &&
    parsed.getMonth() + 1 === month &&
    parsed.getDate() === day
  );
}

function startOfToday(): Date {
  return new Date(today.getFullYear(), today.getMonth(), today.getDate());
}

/** 按「字」截断预览，避免半句悬空与超长换行 */
function truncatePreview(text: string, maxChars = 50): string {
  const chars = Array.from(text);
  if (chars.length <= maxChars) {
    return text;
  }
  return `${chars.slice(0, maxChars).join("")}…`;
}

const latestHistoryEntry = computed(() => historyItems.value[0] ?? null);
const latestHistoryPreview = computed(() =>
  latestHistoryEntry.value ? truncatePreview(latestHistoryEntry.value.preview, 50) : "",
);

</script>

<template>
  <div class="fortune-panel">
    <form class="fortune-form" @submit.prevent="submitForm">
      <section class="card">
        <h2>基本信息</h2>

        <fieldset class="date-row">
          <legend>出生年月日</legend>
          <label>
            年
            <select name="birthYear" v-model="form.birthYear" required>
              <option value="">请选择年份</option>
              <option v-for="year in yearOptions" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </label>
          <label>
            月
            <select name="birthMonth" v-model="form.birthMonth" required>
              <option value="">请选择月份</option>
              <option v-for="month in monthOptions" :key="month" :value="month">
                {{ month }}
              </option>
            </select>
          </label>
          <label>
            日
            <select name="birthDay" v-model="form.birthDay" required>
              <option value="">请选择日期</option>
              <option v-for="day in dayOptions" :key="day" :value="day">
                {{ day }}
              </option>
            </select>
          </label>
        </fieldset>

        <fieldset class="inline-row" data-test="birth-time-gender-row">
          <legend>出生时间与性别</legend>
          <label>
            出生时间
            <input name="birthTime" v-model="form.birthTime" type="text" placeholder="如 18:56 或 凌晨一点左右" />
          </label>
          <label>
            性别
            <select name="gender" v-model="form.gender" required>
              <option>男</option>
              <option>女</option>
              <option>不便透露</option>
            </select>
          </label>
        </fieldset>

        <fieldset class="location-row" data-test="birth-place-row">
          <legend>出生地</legend>
          <label>
            省份
            <select name="province" v-model="form.province" required>
              <option value="">请选择省份</option>
              <option v-for="province in provinceOptions" :key="province" :value="province">
                {{ province }}
              </option>
            </select>
          </label>

          <label>
            城市
            <input name="city" v-model="form.city" type="text" placeholder="杭州市" />
          </label>

          <label>
            区县
            <input name="district" v-model="form.district" type="text" placeholder="西湖区" />
          </label>
        </fieldset>

        <fieldset class="checkbox-group">
          <legend>名字中的五行元素（可选）</legend>
          <label
            v-for="element in elementOptions"
            :key="element"
            class="chip"
            :class="{ selected: form.fiveElements.includes(element) }"
            :data-test="`element-chip-${element}`"
          >
            <input
              v-model="form.fiveElements"
              class="round-checkbox"
              type="checkbox"
              name="fiveElements"
              :value="element"
              :data-test="`element-${element}`"
            />
            {{ element }}
          </label>
        </fieldset>
      </section>

      <section class="card">
        <h2>补充信息</h2>

        <fieldset class="inline-row" data-test="zodiac-mbti-row">
          <legend>星座与 MBTI</legend>
          <label>
            星座
            <select name="zodiac" v-model="form.zodiac">
              <option value="">自动计算或暂不填写</option>
              <option v-for="zodiac in zodiacOptions" :key="zodiac" :value="zodiac">
                {{ zodiac }}
              </option>
            </select>
          </label>
          <label>
            MBTI
            <select name="mbti" v-model="form.mbti">
              <option v-for="mbti in mbtiOptions" :key="mbti" :value="mbti">
                {{ mbti }}
              </option>
            </select>
          </label>
        </fieldset>

        <fieldset class="checkbox-group">
          <legend>当前关注方向</legend>
          <label
            v-for="focus in focusOptions"
            :key="focus"
            class="chip"
            :class="{ selected: form.focusAreas.includes(focus) }"
            :data-test="`focus-chip-${focus}`"
          >
            <input
              v-model="form.focusAreas"
              class="round-checkbox"
              type="checkbox"
              name="focusAreas"
              :value="focus"
              :data-test="`focus-${focus}`"
            />
            {{ focus }}
          </label>
        </fieldset>
      </section>

      <button type="submit" :disabled="loading">
        {{ loading ? "生成中..." : "生成优化提示词" }}
      </button>

      <p v-if="error" class="error">{{ error }}</p>

      <section v-if="prompt" class="card result">
        <div class="result-header">
          <div>
            <h2>优化后提示词</h2>
            <p class="result-hint">请复制到其它大模型中使用；本页不会对您的命盘做解读或下结论。</p>
          </div>
          <button data-test="copy-prompt" class="secondary-button" type="button" @click="copyPrompt">
            {{ copied ? "已复制" : "一键复制" }}
          </button>
        </div>
        <pre>{{ prompt }}</pre>
      </section>

      <section v-if="latestHistoryEntry" class="card history">
        <h2>最近生成记录</h2>
        <button
          data-test="history-item"
          class="history-item"
          type="button"
          @click="showHistoryDetail(latestHistoryEntry.id)"
        >
          <div class="history-meta">
            <time>{{ latestHistoryEntry.createdAt }}</time>
          </div>
          <p class="history-preview">{{ latestHistoryPreview }}</p>
        </button>

        <section v-if="selectedHistory" class="history-detail">
          <h3>历史记录详情</h3>
          <time>{{ selectedHistory.createdAt }}</time>
          <pre>{{ selectedHistory.optimizedPrompt }}</pre>
        </section>
      </section>
    </form>
  </div>
</template>
