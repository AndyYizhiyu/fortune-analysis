import os
from datetime import datetime, timezone, timedelta
from itertools import count

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import HistoryDetail, HistoryListItem, HistoryResponse, OptimizeRequest, OptimizeResponse
from backend.app.services.llm import generate_optimized_prompt
from backend.app.services.prompt import calculate_zodiac


app = FastAPI(title="命理场景提示词生成器（仅代写下游提示词）")


def _cors_origins() -> list[str]:
    raw = os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_history: list[HistoryDetail] = []
_id_sequence = count(1)


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest) -> OptimizeResponse:
    normalized_request = request.model_copy(
        update={"zodiac": request.zodiac or calculate_zodiac(request.birthDate)}
    )
    created_at = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    response = OptimizeResponse(
        id=f"history_{next(_id_sequence):03d}",
        optimizedPrompt=generate_optimized_prompt(normalized_request),
        createdAt=created_at,
    )
    _history.insert(0, HistoryDetail(**response.model_dump()))
    del _history[10:]
    return response


@app.get("/history", response_model=HistoryResponse)
def history() -> HistoryResponse:
    return HistoryResponse(items=[_to_list_item(item) for item in _history])


@app.get("/history/{history_id}", response_model=HistoryDetail)
def history_detail(history_id: str) -> HistoryDetail:
    for item in _history:
        if item.id == history_id:
            return item
    raise HTTPException(status_code=404, detail="历史记录不存在")


def _to_list_item(item: HistoryDetail) -> HistoryListItem:
    return HistoryListItem(
        id=item.id,
        createdAt=item.createdAt,
        preview=item.optimizedPrompt[:50],
    )
