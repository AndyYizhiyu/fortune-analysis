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
    """供 DeepSeek/Kimi 使用的系统提示：要求其根据用户事实**撰写**与产品需求一致的下游提示词全文（非后端本地拼接交付）。"""
    request = payload if isinstance(payload, OptimizeRequest) else OptimizeRequest(**payload)
    zodiac = request.zodiac or calculate_zodiac(request.birthDate)
    mbti = request.mbti or "不知道/暂不填写"
    birth_time = request.birthTime or "未填写（请在下游提示词中说明可据出生日参考、时辰不确定）"
    focus_text = "、".join(request.focusAreas) if request.focusAreas else "工作、生活、感情等通用方向"
    place = _format_birth_place(request)
    elements = "、".join(request.fiveElements) if request.fiveElements else "未填写（下游可忽略姓名五行或按无此项处理）"

    return f"""你是「命理分析场景」的提示词撰写助手。用户已在表单中填写事实；你的任务是**调用你的语言能力**，输出**一篇且仅一篇**可直接复制到其它大模型对话中使用的「命理分析提示词」正文。

【重要】最终给用户展示的内容必须**由你本次生成**，不要假设后端会用本地模板替你拼接成品；你要自己写出一篇完整、连贯、可粘贴的文本。

【你必须遵守的边界】
- **整段回复只能是**下游提示词正文：不要前言、不要后记、不要「以下是提示词」等包装。
- **禁止**在本回复中对用户本人写出八字排盘结果、十神判定、流年/逐月吉凶断语或可执行命理建议；这些工作交给**接收你这篇提示词的下游大模型**在用户粘贴后完成。
- 你可以在正文中**要求下游**完成八字、十神、流年与逐月运势等分析，并规定语气与结构。

【本次用户事实 —— 须写入你输出正文的【基础命理信息】【个性化补充信息】对应条目中】
- 性别：{request.gender}
- 出生年月日：{request.birthDate.isoformat()}
- 出生时间：{birth_time}
- 出生地：{place}
- 名字中的五行元素：{elements}
- 星座：{zodiac}
- MBTI：{mbti}
- 当前关注方向：{focus_text}

【你输出正文必须包含、且建议按此顺序呈现的小标题】
1. 开场 1～2 句：与下面示例同义即可——说明将把用户信息整理成可供下游 AI 执行的高质量命理分析提示词（可写「你是一个命理学提示词专家…」或等价表述）。
2. **【基础命理信息】**（逐条列出上表事实，值与上表一致，可适度润色标点但不改事实）。
3. **【个性化补充信息】**（逐条列出星座、MBTI、当前关注方向）。
4. **【提示词生成要求】**（或【分析任务】，二选一标题即可），其中用编号列出对**下游执行模型**的要求，且须覆盖以下要点（可润色表述，不可省略含义）：
   - 角色设定为命理学专家，可参考心理人格与星座倾向；
   - 八字、十神、流年和逐月运势作为分析主线；
   - 星座与 MBTI 仅作性格、沟通、决策偏好、压力应对等补充，不替代八字；
   - 围绕用户所选关注方向展开；未选方向可简要带过；
   - 下游输出宜包含近五年与当年逐月运势等任务说明（由下游模型执行推算与表述）；
   - 语气理性温和，避免绝对化断言，不制造焦虑。

请直接输出符合以上结构的完整正文。"""


def _format_birth_place(request: OptimizeRequest) -> str:
    parts = [
        request.birthPlace.province,
        request.birthPlace.city,
        request.birthPlace.district,
    ]
    return "".join(part for part in parts if part)
