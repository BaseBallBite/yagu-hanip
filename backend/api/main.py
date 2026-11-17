"""야구한입 백엔드 API 진입점.

실행 (저장소 루트에서):
    .venv/bin/uvicorn backend.api.main:app --reload --port 8000

문서: http://localhost:8000/docs
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.dictionary import router as dictionary_router
from backend.api.explanations import router as explanations_router
from backend.api.games import router as games_router
from backend.api.highlights import router as highlights_router

app = FastAPI(title="야구한입 API", version="0.1.0")

# 프론트 개발 서버(vite, 포트 3000)에서 부를 수 있게 허용. 배포 때는 CORS_ORIGINS 환경 변수로 바꾼다.
origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(dictionary_router)
app.include_router(games_router)
app.include_router(highlights_router)
app.include_router(explanations_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
