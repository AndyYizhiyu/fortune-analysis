from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Gender = Literal["男", "女", "不便透露"]
Element = Literal["金", "木", "水", "火", "土"]
Zodiac = Literal[
    "白羊座",
    "金牛座",
    "双子座",
    "巨蟹座",
    "狮子座",
    "处女座",
    "天秤座",
    "天蝎座",
    "射手座",
    "摩羯座",
    "水瓶座",
    "双鱼座",
]
Mbti = Literal[
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
    "不知道/暂不填写",
]
FocusArea = Literal["工作", "感情", "财运", "学业", "考试", "健康", "人际", "家庭"]


class BirthPlace(BaseModel):
    province: str = Field(min_length=1, max_length=30)
    city: str | None = Field(default=None, max_length=30)
    district: str | None = Field(default=None, max_length=30)


class OptimizeRequest(BaseModel):
    birthDate: date
    birthTime: str | None = Field(default=None, max_length=30)
    birthPlace: BirthPlace
    gender: Gender
    fiveElements: list[Element] = Field(min_length=1, max_length=5)
    zodiac: Zodiac | None = None
    mbti: Mbti | None = None
    focusAreas: list[FocusArea] = Field(default_factory=list)

    @field_validator("birthDate")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value.year < 1945 or value.year > 2035:
            raise ValueError("出生年份必须在 1945 到 2035 之间")
        if value > date.today():
            raise ValueError("出生日期不能晚于今天")
        return value

    @field_validator("birthTime")
    @classmethod
    def normalize_birth_time(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class OptimizeResponse(BaseModel):
    id: str
    optimizedPrompt: str
    createdAt: str


class HistoryListItem(BaseModel):
    id: str
    createdAt: str
    preview: str


class HistoryDetail(BaseModel):
    id: str
    createdAt: str
    optimizedPrompt: str


class HistoryResponse(BaseModel):
    items: list[HistoryListItem]
