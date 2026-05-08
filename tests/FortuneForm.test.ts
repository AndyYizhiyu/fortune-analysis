import { flushPromises, mount } from "@vue/test-utils";

import App from "../src/App.vue";
import FortuneForm from "../src/components/FortuneForm.vue";

function mockFetchWithHistory(prompt = "结构化命理提示词") {
  return vi.fn(async (url: string, options?: RequestInit) => {
    if (url === "/api/history") {
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              id: "history_000",
              createdAt: "2026-05-08 16:00",
              preview:
                "历史提示词内容历史提示词内容历史提示词内容历史提示词内容历史提示词历史提示词内容历史提示词内容历史提示词内容",
            },
          ],
        }),
      };
    }

    if (url.startsWith("/api/history/")) {
      const id = url.slice("/api/history/".length);
      return {
        ok: true,
        json: async () => ({
          id,
          createdAt: id === "history_001" ? "2026-05-08 17:00" : "2026-05-08 16:00",
          optimizedPrompt: id === "history_001" ? prompt : "历史提示词完整内容",
        }),
      };
    }

    if (url === "/api/optimize" && options?.method === "POST") {
      return {
        ok: true,
        json: async () => ({
          id: "history_001",
          originalInput: {},
          optimizedPrompt: prompt,
          createdAt: "2026-05-08 17:00",
        }),
      };
    }

    throw new Error(`Unexpected request: ${url}`);
  });
}

describe("FortuneForm", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  it("可不选五行元素仍成功提交并请求优化接口", async () => {
    const fetchMock = mockFetchWithHistory();
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(FortuneForm);
    await flushPromises();
    await wrapper.get('[name="birthYear"]').setValue("1995");
    await wrapper.get('[name="birthMonth"]').setValue("8");
    await wrapper.get('[name="birthDay"]').setValue("18");
    await wrapper.get('[name="province"]').setValue("浙江省");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    const optimizeCall = fetchMock.mock.calls.find(([url]) => url === "/api/optimize");
    expect(optimizeCall).toBeDefined();
    const body = JSON.parse(optimizeCall![1]!.body as string);
    expect(body.fiveElements).toEqual([]);
    expect(fetchMock).toHaveBeenCalledWith("/api/optimize", expect.anything());
  });

  it("拆分年月日输入后自动计算星座，并通过复选按钮提交全部关注方向", async () => {
    const fetchMock = mockFetchWithHistory();
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(FortuneForm);
    await flushPromises();

    await wrapper.get('[name="birthYear"]').setValue("1995");
    await wrapper.get('[name="birthMonth"]').setValue("8");
    await wrapper.get('[name="birthDay"]').setValue("18");
    expect(wrapper.get('[name="birthYear"]').element.tagName).toBe("SELECT");
    expect(wrapper.get('[name="birthMonth"]').element.tagName).toBe("SELECT");
    expect(wrapper.get('[name="birthDay"]').element.tagName).toBe("SELECT");
    expect((wrapper.get('[name="zodiac"]').element as HTMLSelectElement).value).toBe("狮子座");

    await wrapper.get('[name="birthTime"]').setValue("18:56");
    expect(wrapper.get('[name="province"]').element.tagName).toBe("SELECT");
    await wrapper.get('[name="province"]').setValue("浙江省");
    await wrapper.get('[name="city"]').setValue("杭州市");
    await wrapper.get('[name="gender"]').setValue("女");
    await wrapper.get('[data-test="element-木"]').setValue(true);
    await wrapper.get('[data-test="element-水"]').setValue(true);
    expect(wrapper.get('[data-test="element-chip-木"]').classes()).toContain("selected");
    await wrapper.get('[name="mbti"]').setValue("ENFP");
    for (const focus of ["工作", "感情", "财运", "学业", "考试", "健康", "人际", "家庭"]) {
      await wrapper.get(`[data-test="focus-${focus}"]`).setValue(true);
    }
    expect(wrapper.get('[data-test="focus-chip-工作"]').classes()).toContain("selected");
    expect(wrapper.text()).toContain("当前关注方向");
    expect(wrapper.text()).not.toContain("不限数量");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/optimize",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    );
    const optimizeCall = fetchMock.mock.calls.find(([url]) => url === "/api/optimize");
    expect(optimizeCall).toBeDefined();
    const request = optimizeCall![1];
    expect(request).toBeDefined();
    expect(JSON.parse(request!.body as string)).toMatchObject({
      birthDate: "1995-08-18",
      fiveElements: ["木", "水"],
      focusAreas: ["工作", "感情", "财运", "学业", "考试", "健康", "人际", "家庭"],
    });
    expect(wrapper.text()).toContain("结构化命理提示词");
  });

  it("支持一键复制优化后的提示词", async () => {
    const fetchMock = mockFetchWithHistory("可复制的提示词");
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(FortuneForm);
    await flushPromises();
    await wrapper.get('[name="birthYear"]').setValue("1995");
    await wrapper.get('[name="birthMonth"]').setValue("8");
    await wrapper.get('[name="birthDay"]').setValue("18");
    await wrapper.get('[name="province"]').setValue("浙江省");
    await wrapper.get('[data-test="element-木"]').setValue(true);
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    await wrapper.get('[data-test="copy-prompt"]').trigger("click");

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("可复制的提示词");
    expect(wrapper.text()).toContain("已复制");
  });

  it("支持暗黑模式切换", async () => {
    vi.stubGlobal("fetch", mockFetchWithHistory());
    const wrapper = mount(App, { attachTo: document.body });
    await flushPromises();

    const themeButton = wrapper.get('[data-test="theme-toggle"]');
    expect(themeButton.text()).toBe("☀");
    expect(themeButton.attributes("aria-label")).toBe("切换暗黑模式");
    expect(themeButton.classes()).toContain("header-corner-button");
    expect(themeButton.text()).not.toContain("切换到");
    expect(document.documentElement.dataset.theme).toBe("light");
    await themeButton.trigger("click");

    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(wrapper.get(".app-shell").classes()).toContain("dark");
  });

  it("五行元素和关注方向使用圆形勾选控件", async () => {
    vi.stubGlobal("fetch", mockFetchWithHistory());
    const wrapper = mount(FortuneForm);
    await flushPromises();

    expect(wrapper.get('[data-test="element-木"]').classes()).toContain("round-checkbox");
    expect(wrapper.get('[data-test="focus-工作"]').classes()).toContain("round-checkbox");
  });

  it("省份城市区县在同一行布局中展示", async () => {
    vi.stubGlobal("fetch", mockFetchWithHistory());
    const wrapper = mount(FortuneForm);
    await flushPromises();

    const locationRow = wrapper.get('[data-test="birth-place-row"]');
    expect(locationRow.classes()).toContain("location-row");
    expect(locationRow.find('[name="province"]').element.tagName).toBe("SELECT");
    expect(locationRow.find('[name="province"]').exists()).toBe(true);
    expect(locationRow.find('[name="city"]').exists()).toBe(true);
    expect(locationRow.find('[name="district"]').exists()).toBe(true);
  });

  it("拒绝超过当前日期的出生日期，不发起生成请求", async () => {
    const fetchMock = mockFetchWithHistory();
    vi.stubGlobal("fetch", fetchMock);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    const wrapper = mount(FortuneForm);
    await flushPromises();
    await wrapper.get('[name="birthYear"]').setValue(String(tomorrow.getFullYear()));
    await wrapper.get('[name="birthMonth"]').setValue(String(tomorrow.getMonth() + 1));
    await wrapper.get('[name="birthDay"]').setValue(String(tomorrow.getDate()));
    await wrapper.get('[name="province"]').setValue("浙江省");
    await wrapper.get('[data-test="element-木"]').setValue(true);
    await wrapper.get("form").trigger("submit");

    expect(wrapper.text()).toContain("出生日期不能晚于今天");
    expect(fetchMock).not.toHaveBeenCalledWith("/api/optimize", expect.anything());
  });

  it("出生时间与性别、星座与 MBTI 使用同一行栅格布局", async () => {
    vi.stubGlobal("fetch", mockFetchWithHistory());
    const wrapper = mount(FortuneForm);
    await flushPromises();

    const birthGenderRow = wrapper.get('[data-test="birth-time-gender-row"]');
    expect(birthGenderRow.classes()).toContain("inline-row");
    expect(birthGenderRow.find('[name="birthTime"]').exists()).toBe(true);
    expect(birthGenderRow.find('[name="gender"]').exists()).toBe(true);

    const zodiacMbtiRow = wrapper.get('[data-test="zodiac-mbti-row"]');
    expect(zodiacMbtiRow.classes()).toContain("inline-row");
    expect(zodiacMbtiRow.find('[name="zodiac"]').exists()).toBe(true);
    expect(zodiacMbtiRow.find('[name="mbti"]').exists()).toBe(true);
  });

  it("展示最近生成的历史记录前50字，不展示用户输入，并支持查看详情", async () => {
    const fetchMock = mockFetchWithHistory("新生成提示词");
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(FortuneForm);
    await flushPromises();
    expect(wrapper.text()).toContain("2026-05-08 16:00");
    expect(wrapper.text()).toContain(
      "历史提示词内容历史提示词内容历史提示词内容历史提示词内容历史提示词历史提示词内容历史提示词内容历史提…",
    );
    expect(wrapper.text()).not.toContain("历史摘要");
    expect(wrapper.text()).not.toContain("用户信息");

    await wrapper.get('[data-test="history-item"]').trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("历史提示词完整内容");

    await wrapper.get('[name="birthYear"]').setValue("1995");
    await wrapper.get('[name="birthMonth"]').setValue("8");
    await wrapper.get('[name="birthDay"]').setValue("18");
    await wrapper.get('[name="province"]').setValue("浙江省");
    await wrapper.get('[data-test="element-木"]').setValue(true);
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("最近生成记录");
    expect(wrapper.text()).toContain("新生成提示词");
    expect(wrapper.text()).toContain("2026-05-08 17:00");
    expect(wrapper.text()).not.toContain("2026-05-08 16:00");
    expect(wrapper.findAll('[data-test="history-item"]')).toHaveLength(1);
    expect(wrapper.find('[data-test="copy-prompt"]').exists()).toBe(true);
  });

  it("生成失败时展示后端返回的具体错误原因", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (url === "/api/history") {
        return { ok: true, json: async () => ({ items: [] }) };
      }
      if (url === "/api/optimize" && options?.method === "POST") {
        return {
          ok: false,
          json: async () => ({
            detail: [{ msg: "出生日期不能晚于今天" }],
          }),
        };
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(FortuneForm);
    await flushPromises();
    await wrapper.get('[name="birthYear"]').setValue("1995");
    await wrapper.get('[name="birthMonth"]').setValue("8");
    await wrapper.get('[name="birthDay"]').setValue("18");
    await wrapper.get('[name="province"]').setValue("浙江省");
    await wrapper.get('[data-test="element-木"]').setValue(true);
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("出生日期不能晚于今天");
    expect(wrapper.text()).not.toContain("提示词生成失败，请检查输入后重试");
  });
});
