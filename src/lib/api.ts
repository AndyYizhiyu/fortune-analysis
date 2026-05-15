export interface OptimizePayload {
  birthDate: string;
  birthTime?: string | null;
  birthPlace: {
    province: string;
    city?: string | null;
    district?: string | null;
  };
  gender: string;
  fiveElements: string[];
  zodiac?: string | null;
  mbti?: string | null;
  focusAreas: string[];
}

export interface OptimizeResponse {
  id: string;
  originalInput?: OptimizePayload;
  optimizedPrompt: string;
  createdAt: string;
}

export interface HistoryListItem {
  id: string;
  createdAt: string;
  preview: string;
}

export interface HistoryDetail {
  id: string;
  createdAt: string;
  optimizedPrompt: string;
}

/** 生产环境在构建时设置 VITE_API_BASE_URL（后端根 URL，无末尾斜杠）；本地留空走 Vite /api 代理。 */
function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (typeof raw !== "string" || !raw.trim()) {
    return "";
  }
  return raw.trim().replace(/\/$/, "");
}

function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const base = apiBase();
  if (!base) {
    return `/api${p}`;
  }
  return `${base}${p}`;
}

export async function optimizePrompt(payload: OptimizePayload): Promise<OptimizeResponse> {
  const response = await fetch(apiUrl("/optimize"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function fetchHistory(): Promise<HistoryListItem[]> {
  const response = await fetch(apiUrl("/history"));

  if (!response.ok) {
    throw new Error("历史记录加载失败");
  }

  const body = (await response.json()) as { items: HistoryListItem[] };
  return body.items;
}

export async function fetchHistoryDetail(id: string): Promise<HistoryDetail> {
  const response = await fetch(apiUrl(`/history/${id}`));

  if (!response.ok) {
    throw new Error("历史记录详情加载失败");
  }

  return response.json();
}

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      return body.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join("；");
    }
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (typeof body.message === "string") {
      return body.message;
    }
  } catch {
    // Ignore malformed error bodies and fall through to a stable message.
  }

  return "提示词生成失败，请检查输入后重试";
}
