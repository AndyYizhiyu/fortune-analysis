from datetime import date
from typing import Any

from backend.app.models import OptimizeRequest


ZODIAC_RANGES = [
    ((1, 20), "水瓶座"),
    ((2, 19), "双鱼座"),
    ((3, 21), "白羊座"),
    ((4, 20), "金牛座"),
    ((5, 21), "双子座"),
    ((6, 22), "巨蟹座"),
    ((7, 23), "狮子座"),
    ((8, 23), "处女座"),
    ((9, 23), "天秤座"),
    ((10, 24), "天蝎座"),
    ((11, 23), "射手座"),
    ((12, 22), "摩羯座"),
]


def calculate_zodiac(birth_date: str | date) -> str:
    if isinstance(birth_date, str):
        parsed_date = date.fromisoformat(birth_date)
    else:
        parsed_date = birth_date

    month_day = (parsed_date.month, parsed_date.day)
    zodiac = "摩羯座"
    for start, name in ZODIAC_RANGES:
        if month_day >= start:
            zodiac = name
        else:
            break
    return zodiac


def build_optimized_prompt(payload: OptimizeRequest | dict[str, Any]) -> str:
    request = payload if isinstance(payload, OptimizeRequest) else OptimizeRequest(**payload)
    zodiac = request.zodiac or calculate_zodiac(request.birthDate)
    mbti = request.mbti or "不知道/暂不填写"
    birth_time = request.birthTime or "未填写，按已有出生信息参考分析"
    focus_text = "、".join(request.focusAreas) if request.focusAreas else "工作、生活、感情等通用方向"
    place = _format_birth_place(request)

    return f"""你是一位命理学专家，同时可参考心理人格分析和星座性格倾向，为用户生成理性、温和、可执行的命理分析。

【用户信息】
- 性别：{request.gender}
- 出生年月日：{request.birthDate.isoformat()}
- 出生时间：{birth_time}
- 出生地：{place}
- 名字中的五行元素：{"、".join(request.fiveElements)}
- 星座：{zodiac}
- MBTI：{mbti}
- 重点关注：{focus_text}

【分析任务】
1. 以八字、十神、流年和逐月运势为主线，分析近五年整体趋势和今年逐月变化。
2. 结合名字中的五行元素，说明可参考的五行倾向和提醒。
3. 结合星座和 MBTI 补充性格倾向、沟通方式、决策偏好和压力应对方式，但不要替代八字分析。
4. 围绕重点关注方向输出具体建议；未选择的方向可简要带过。
5. 给出生活、工作、感情、学习或财务方面的可执行建议。

【输出约束】
- 避免绝对化断言，避免制造焦虑。
- 使用“参考、倾向、建议、可以尝试”等表达。
- 内容结构清晰，适合用户直接阅读和复制。"""


def _format_birth_place(request: OptimizeRequest) -> str:
    parts = [
        request.birthPlace.province,
        request.birthPlace.city,
        request.birthPlace.district,
    ]
    return "".join(part for part in parts if part)
