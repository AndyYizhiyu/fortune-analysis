import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import get_llm_settings
from backend.app.services.llm import call_chat_completion
from backend.app.services.prompt import build_optimized_prompt, calculate_zodiac


VALID_PAYLOAD = {
    "birthDate": "1995-08-18",
    "birthTime": "18:56",
    "birthPlace": {
        "province": "浙江省",
        "city": "杭州市",
        "district": "西湖区",
    },
    "gender": "女",
    "fiveElements": ["木", "水"],
    "zodiac": "狮子座",
    "mbti": "ENFP",
    "focusAreas": ["工作", "感情", "财运"],
}


class FortuneApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_calculates_zodiac_from_birth_date(self):
        self.assertEqual(calculate_zodiac("1995-08-18"), "狮子座")
        self.assertEqual(calculate_zodiac("1995-12-22"), "摩羯座")

    def test_builds_llm_instruction_for_requirement_shaped_downstream_prompt(self):
        prompt = build_optimized_prompt(VALID_PAYLOAD)

        self.assertIn("【基础命理信息】", prompt)
        self.assertIn("【个性化补充信息】", prompt)
        self.assertIn("提示词生成要求", prompt)
        self.assertIn("禁止", prompt)
        self.assertIn("狮子座", prompt)
        self.assertIn("ENFP", prompt)
        self.assertIn("工作、感情、财运", prompt)
        self.assertIn("八字、十神、流年", prompt)
        self.assertIn("由你本次生成", prompt)

    def test_accepts_empty_five_elements(self):
        payload = {**VALID_PAYLOAD, "fiveElements": []}
        with patch("backend.app.main.generate_optimized_prompt", return_value="ok"):
            response = self.client.post("/optimize", json=payload)

        self.assertEqual(response.status_code, 200)

    def test_build_prompt_handles_empty_five_elements(self):
        prompt = build_optimized_prompt({**VALID_PAYLOAD, "fiveElements": []})

        self.assertIn("未填写", prompt)
        self.assertIn("【基础命理信息】", prompt)

    def test_optimize_returns_prompt_and_saves_history(self):
        with patch("backend.app.main.generate_optimized_prompt", return_value="模型生成的优化提示词"):
            response = self.client.post("/optimize", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["optimizedPrompt"], "模型生成的优化提示词")
        self.assertIn("createdAt", body)
        self.assertRegex(body["createdAt"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

        history = self.client.get("/history")
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(len(history.json()["items"]), 1)

    def test_history_list_hides_user_input_and_returns_preview(self):
        with patch("backend.app.main.generate_optimized_prompt", return_value="模型生成的优化提示词" * 5):
            response = self.client.post("/optimize", json=VALID_PAYLOAD)
        history = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        item = history.json()["items"][0]
        self.assertEqual(set(item.keys()), {"id", "createdAt", "preview"})
        self.assertLessEqual(len(item["preview"]), 50)
        self.assertRegex(item["createdAt"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

    def test_history_detail_returns_full_prompt(self):
        with patch("backend.app.main.generate_optimized_prompt", return_value="模型生成的完整优化提示词"):
            created = self.client.post("/optimize", json=VALID_PAYLOAD).json()

        response = self.client.get(f"/history/{created['id']}")

        self.assertEqual(response.status_code, 200)
        detail = response.json()
        self.assertEqual(detail["id"], created["id"])
        self.assertEqual(detail["optimizedPrompt"], created["optimizedPrompt"])
        self.assertNotIn("originalInput", detail)

    def test_accepts_all_focus_areas_without_count_limit(self):
        payload = {
            **VALID_PAYLOAD,
            "focusAreas": ["工作", "感情", "财运", "学业", "考试", "健康", "人际", "家庭"],
        }

        with patch("backend.app.main.generate_optimized_prompt", return_value="工作、感情、财运、学业、考试、健康、人际、家庭"):
            response = self.client.post("/optimize", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("工作、感情、财运、学业、考试、健康、人际、家庭", response.json()["optimizedPrompt"])

    def test_rejects_birth_date_after_today(self):
        payload = {
            **VALID_PAYLOAD,
            "birthDate": (date.today() + timedelta(days=1)).isoformat(),
        }

        response = self.client.post("/optimize", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_default_llm_provider_is_deepseek_v4_flash(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = get_llm_settings()

        self.assertEqual(settings.provider, "deepseek")
        self.assertEqual(settings.model, "deepseek-v4-flash")
        self.assertEqual(settings.base_url, "https://api.deepseek.com")

    def test_kimi_provider_uses_kimi_k25_model(self):
        with patch.dict(
            "os.environ",
            {"LLM_PROVIDER": "kimi", "KIMI_API_KEY": "kimi-key"},
            clear=True,
        ):
            settings = get_llm_settings()

        self.assertEqual(settings.provider, "kimi")
        self.assertEqual(settings.model, "kimi-k2.5")
        self.assertEqual(settings.api_key, "kimi-key")
        self.assertEqual(settings.base_url, "https://api.moonshot.ai/v1")

    def test_missing_api_key_returns_clear_error(self):
        with patch("backend.app.config._load_env_file", return_value={}):
            with patch.dict("os.environ", {"LLM_PROVIDER": "deepseek"}, clear=True):
                with self.assertRaises(HTTPException) as context:
                    call_chat_completion("系统提示词")

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("缺少 DeepSeek API Key", context.exception.detail)

    def test_call_chat_completion_uses_openai_compatible_payload(self):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "模型输出"}}]}
        response.raise_for_status.return_value = None

        with patch.dict("os.environ", {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "deepseek-key"}, clear=True):
            with patch("backend.app.services.llm.httpx.post", return_value=response) as post:
                result = call_chat_completion("系统提示词")

        self.assertEqual(result, "模型输出")
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.deepseek.com/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer deepseek-key")
        self.assertEqual(kwargs["json"]["model"], "deepseek-v4-flash")
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "system")
        user_content = kwargs["json"]["messages"][1]["content"]
        self.assertIn("禁止", user_content)
        self.assertIn("命理解读", user_content)


if __name__ == "__main__":
    unittest.main()
