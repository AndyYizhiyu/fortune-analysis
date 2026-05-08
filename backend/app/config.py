import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: str | None
    base_url: str
    model: str


def get_llm_settings() -> LLMSettings:
    env = _load_env_file()
    provider = _get_env("LLM_PROVIDER", env, "deepseek").lower()

    if provider == "kimi":
        return LLMSettings(
            provider="kimi",
            api_key=_get_env("KIMI_API_KEY", env),
            base_url=_get_env("KIMI_BASE_URL", env, "https://api.moonshot.ai/v1").rstrip("/"),
            model=_get_env("KIMI_MODEL", env, "kimi-k2.5"),
        )

    return LLMSettings(
        provider="deepseek",
        api_key=_get_env("DEEPSEEK_API_KEY", env),
        base_url=_get_env("DEEPSEEK_BASE_URL", env, "https://api.deepseek.com").rstrip("/"),
        model=_get_env("DEEPSEEK_MODEL", env, "deepseek-v4-flash"),
    )


def _get_env(key: str, env_file_values: dict[str, str], default: str | None = None) -> str | None:
    return os.environ.get(key) or env_file_values.get(key) or default


def _load_env_file() -> dict[str, str]:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
