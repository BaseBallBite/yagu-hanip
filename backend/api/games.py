"""경기·플레이 조회 API (B4 저장소를 읽음). 프론트 경기 화면용.

DB가 없으면 503을 돌려준다. 먼저: .venv/bin/python -m backend.game.store build

엔드포인트 (접두어 /games):
    GET /games                              경기 목록 (date=YYYY-MM-DD, team=KIA 로 거르기)
    GET /games/{game_id}                    경기 정보 (팀, 최종 점수, 플레이 수)
    GET /games/{game_id}/plays              플레이 목록 + 상태 전/후 (B2)
          ?from_seq=1&limit=100             순번 범위
          &event_type=single,home_run       유형으로 거르기 (쉼표 구분)
          &facts=true                       F 목록 포함 (B3)
          &pitch=true                       투구 정보 포함 (B3: 구종, 구속, 존, 궤적)
    GET /games/{game_id}/plays/{seq}        플레이 1개 상세 (F, 투구 포함)
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from backend.game import store

router = APIRouter(prefix="/games", tags=["games"])


@lru_cache(maxsize=1)
def get_con():
    return store.connect()


def _con():
    try:
        return get_con()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


def _game_or_404(con, game_id: str) -> dict:
    game = store.get_game(con, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail=f"경기를 찾을 수 없습니다: {game_id}")
    return game


@router.get("")
def games(date: str | None = None, team: str | None = None) -> dict:
    items = store.list_games(_con(), date=date, team=team)
    return {"count": len(items), "games": items}


@router.get("/{game_id}")
def game(game_id: str) -> dict:
    return _game_or_404(_con(), game_id)


@router.get("/{game_id}/plays")
def plays(
    game_id: str,
    from_seq: int = Query(1, ge=1),
    limit: int | None = Query(None, ge=1, le=2000),
    event_type: str | None = Query(None, description="쉼표로 구분: single,home_run"),
    facts: bool = False,
    pitch: bool = False,
) -> dict:
    con = _con()
    g = _game_or_404(con, game_id)
    types = [t.strip() for t in event_type.split(",") if t.strip()] if event_type else None
    items = store.list_plays(con, game_id, from_seq=from_seq, limit=limit, event_types=types,
                             with_facts=facts, with_pitch=pitch)
    return {"game_id": game_id, "away": g["away"], "home": g["home"],
            "count": len(items), "plays": items}


@router.get("/{game_id}/plays/{seq}")
def play(game_id: str, seq: int) -> dict:
    con = _con()
    _game_or_404(con, game_id)
    p = store.get_play(con, game_id, seq)
    if p is None:
        raise HTTPException(status_code=404, detail=f"{game_id} 에 순번 {seq} 플레이가 없습니다")
    return {"game_id": game_id} | p
