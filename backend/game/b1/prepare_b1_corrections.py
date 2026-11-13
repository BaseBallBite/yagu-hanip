
import argparse
import json
from pathlib import Path


def load_rows(data_dir, game_id, inning):
    path = data_dir / "games" / game_id / f"inning_{inning:02d}.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    relay = obj["result"]["textRelayData"]

    if relay["gameId"] != game_id:
        raise ValueError(f"경기 ID 불일치: {path}")

    rows = []
    for block in relay["textRelays"]:
        for item in block.get("textOptions", []):
            if "seqno" not in item:
                continue
            rows.append({
                "seqno": item["seqno"],
                "text": item.get("text"),
                "inning": int(block["inn"]),
                "half": "top" if str(block["homeOrAway"]) == "0" else "bottom",
                "state": item.get("currentGameState", {}),
            })
    return rows


def check(rows, seqno, expected_text, half=None):
    found = [
        r for r in rows
        if r["seqno"] == seqno
        and r["text"] == expected_text
        and (half is None or r["half"] == half)
    ]
    if len(found) != 1:
        raise ValueError(
            f"원본 불일치: seqno={seqno}, text={expected_text}, "
            f"일치 수={len(found)}"
        )
    return found[0]


def main(data_dir, output):
    a = "20260415WOHT02026"
    b = "20260401HTLG02026"
    c = "20260415SSHH02026"
    d = "20260822HTWO02026"

    r1 = load_rows(data_dir, a, 1)
    r2 = load_rows(data_dir, b, 5)
    r3 = load_rows(data_dir, c, 8)
    r7 = load_rows(data_dir, d, 7)
    r8 = load_rows(data_dir, d, 8)

    # 1. 이주형 첫 타석 누락 확인
    check(r1, 6, "2번타자 안치홍", "top")
    assert not any(
        r["half"] == "top" and r["seqno"] < 6 for r in r1
    ), "1번: 예상과 다른 선행 기록이 있습니다."

    # 2. 잘못된 주자 진루 기록 확인
    check(r2, 327, "오지환 : 1루수 땅볼 아웃 (1루수 1루 터치아웃)", "bottom")
    wrong = check(r2, 328, "2루주자 문성주 : 3루까지 진루", "bottom")
    assert str(wrong["state"].get("base2")) == "0"

    # 3. 김재상 진루 행 누락 확인
    check(r3, 597, "류지혁 : 볼넷", "top")
    check(r3, 598, "6번타자 박세혁", "top")
    assert any("대주자 김재상" in (r["text"] or "") for r in r3)
    assert not any("김재상 : 2루까지 진루" in (r["text"] or "") for r in r3)

    # 4. 이닝 경계 seqno 중복 확인
    check(r7, 375, "추재현 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)", "bottom")
    check(r8, 375, "8회초 KIA 공격", "top")
    check(r8, 398, "박정우 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)", "top")
    check(r8, 398, "8회말 키움 공격", "bottom")
    assert not any(r["seqno"] in (376, 399) for r in r8)

    corrections = {
        "schema_version": "b1-manual-corrections-v1",
        "raw_files_modified": False,
        "cases": [
            {
                "game_id": a,
                "inning": 1,
                "half": "top",
                "action": "insert_before",
                "anchor_seqno": 6,
                "anchor_text": "2번타자 안치홍",
                "records": [
                    "1회초 키움 공격",
                    "1번타자 이주형",
                    "1구 스트라이크",
                    "2구 볼",
                    "3구 타격",
                    "이주형 : 좌익수 앞 1루타"
                ],
                "evidence": {
                    "source_gap": "네이버 API 및 앱에서 누락 확인",
                    "hit": "경기 기사 및 중계 화면 대조",
                    "pitch_sequence": "팀원 중계 영상 확인",
                    "original_pitch_ids_available": False
                },
                "create_original_seqno": False
            },
            {
                "game_id": b,
                "inning": 5,
                "half": "bottom",
                "action": "exclude",
                "target_seqno": 328,
                "target_text": "2루주자 문성주 : 3루까지 진루",
                "expected_state_after_327": {
                    "outs": 2,
                    "first": None,
                    "second": "문성주",
                    "third": "박동원"
                },
                "note": "원본 seqno 327의 주자 상태도 오류이므로 B2 수정 필요",
                "evidence": "경기 중계 영상 및 5회말 무득점 확인"
            },
            {
                "game_id": c,
                "inning": 8,
                "half": "top",
                "action": "insert_after",
                "anchor_seqno": 597,
                "anchor_text": "류지혁 : 볼넷",
                "records": [
                    "1루주자 김재상 : 2루까지 진루"
                ],
                "expected_state_after_597": {
                    "outs": 2,
                    "first": "류지혁",
                    "second": "김재상",
                    "third": "박승규"
                },
                "create_original_seqno": False,
                "evidence": "볼넷에 따른 강제 진루 및 경기 기록 대조"
            },
            {
                "game_id": d,
                "inning": 8,
                "action": "preserve_original",
                "colliding_seqnos": [375, 398],
                "note": "이닝 경계의 번호 중복. 누락 플레이 확인되지 않음"
            }
        ]
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(corrections, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print("원본 4건 확인 조건 통과")
    print(f"보완 규칙 생성: {output}")
    print("기존 원본 JSON 변경 없음")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path,
        default=Path("b1_manual_corrections_v1.json")
    )
    args = parser.parse_args()
    main(args.data, args.out)
