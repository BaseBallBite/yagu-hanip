"""B12 하이라이트 장면 조회 API. 영상 재생 시간 → 그 순간의 경기 상황 카드.

장면 표(ai/highlight/output)를 SQLite에 넣어 둔 것을 읽는다. DB가 없으면 첫 요청 때 만든다.
AI 호출은 없다. 평가용 경기는 들어 있지 않다 (games.csv 의 demo 경기만).
경기 DB(B4 yagu.sqlite)가 있으면 장면에 유형 태그(prev_type_tags, result_type_tags)를 붙인다.

엔드포인트 (접두어 /highlights):
    GET /highlights                         하이라이트 영상 목록 (video_id, game_id, 팀)
    GET /highlights/{video_id}              영상 정보
    GET /highlights/{video_id}/scenes       장면 표 전체 (추천: 처음에 한 번 받아서 프론트가 시간으로 찾기)
    GET /highlights/{video_id}/scene?t=757.3  재생 시간 t초의 장면 하나
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from backend.game import store as game_store
from backend.highlight import store

router = APIRouter(prefix="/highlights", tags=["highlights"])


@lru_cache(maxsize=1)
def get_con():
    return store.connect()


@lru_cache(maxsize=1)
def get_game_con():
    """유형 태그용 경기 DB. 없으면 None (태그만 빠지고 나머지는 그대로 동작)."""
    try:
        return game_store.connect()
    except FileNotFoundError:
        return None


def _video_or_404(con, video_id: str) -> dict:
    h = store.get_highlight(con, video_id)
    if h is None:
        raise HTTPException(status_code=404, detail=f"하이라이트 영상을 찾을 수 없습니다: {video_id}")
    return h


@router.get("")
def highlights() -> dict:
    items = store.list_highlights(get_con())
    return {"count": len(items), "highlights": items}


@router.get("/{video_id}")
def highlight(video_id: str) -> dict:
    return _video_or_404(get_con(), video_id)


@router.get("/{video_id}/scenes")
def scenes(video_id: str) -> dict:
    con = get_con()
    h = _video_or_404(con, video_id)
    items = store.add_type_tags(store.list_scenes(con, video_id), get_game_con())
    return h | {"count": len(items), "scenes": items}


@router.get("/{video_id}/scene")
def scene(video_id: str, t: float = Query(..., ge=0, description="영상 재생 시간(초)")) -> dict:
    con = get_con()
    _video_or_404(con, video_id)
    return store.add_type_tags([store.scene_at(con, video_id, t)], get_game_con())[0]
