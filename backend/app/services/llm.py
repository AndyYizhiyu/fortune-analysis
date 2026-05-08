import httpx
from fastapi import HTTPException

from backend.app.config import LLMSettings, get_llm_settings
from backend.app.models import OptimizeRequest
from backend.app.services.prompt import build_optimized_prompt


def generate_optimized_prompt(request: OptimizeRequest) -> str:
    system_prompt = build_optimized_prompt(request)
    return call_chat_completion(system_prompt)


def call_chat_completion(system_prompt: str) -> str:
    settings = get_llm_settings()
    _ensure_api_key(settings)

    url = f"{settings.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    payload = _build_payload(settings, system_prompt)
    timeout = httpx.Timeout(180.0, connect=10.0, read=180.0, write=30.0, pool=10.0)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            break
        except httpx.ReadTimeout as exc:
            last_error = exc
        except httpx.ConnectTimeout as exc:
            last_error = exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"AI 服务调用失败：{exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"AI 服务连接失败：{exc}") from exc
    else:
        raise HTTPException(status_code=504, detail=f"AI 服务响应超时：{last_error}") from last_error

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise HTTPException(status_code=502, detail="AI 服务未返回有效内容")
    return content


def _build_payload(settings: LLMSettings, system_prompt: str) -> dict:
    # 生成内容可能较长；适度约束 max_tokens 降低极端超时概率
    return {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "请严格按系统说明：只输出一段可复制到其它大模型对话中的提示词全文；"
                    "禁止在本回复中对用户做任何命理解读、运势结论或具体建议。"
                ),
            },
        ],
        "temperature": 0.5,
        "max_tokens": 1800,
    }


def _ensure_api_key(settings: LLMSettings) -> None:
    if settings.api_key:
        return

    provider_label = "Kimi" if settings.provider == "kimi" else "DeepSeek"
    raise HTTPException(status_code=500, detail=f"缺少 {provider_label} API Key，请检查 .env 配置")
