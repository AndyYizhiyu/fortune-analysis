import unittest
from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app
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

    def test_builds_structured_prompt_with_personality_context(self):
        prompt = build_optimized_prompt(VALID_PAYLOAD)

        self.assertIn("命理学专家", prompt)
        self.assertIn("八字、十神、流年和逐月运势", prompt)
        self.assertIn("星座：狮子座", prompt)
        self.assertIn("MBTI：ENFP", prompt)
        self.assertIn("重点关注：工作、感情、财运", prompt)
        self.assertIn("避免绝对化断言", prompt)

    def test_optimize_returns_prompt_and_saves_history(self):
        response = self.client.post("/optimize", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("optimizedPrompt", body)
        self.assertIn("createdAt", body)
        self.assertRegex(body["createdAt"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

        history = self.client.get("/history")
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(len(history.json()["items"]), 1)

    def test_history_list_hides_user_input_and_returns_preview(self):
        response = self.client.post("/optimize", json=VALID_PAYLOAD)
        history = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        item = history.json()["items"][0]
        self.assertEqual(set(item.keys()), {"id", "createdAt", "preview"})
        self.assertLessEqual(len(item["preview"]), 50)
        self.assertRegex(item["createdAt"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

    def test_history_detail_returns_full_prompt(self):
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


if __name__ == "__main__":
    unittest.main()
