
"""Preflight checks before rebuilding corrected B1 v2.
Read-only: never modifies source files.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OVERLAY = BASE / "b1_verified_overlay_v1"

A = "20260415WOHT02026"
B = "20260401HTLG02026"
C = "20260415SSHH02026"
D = "20260822HTWO02026"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(condition, message):
    if not condition:
        raise ValueError("FAILED: " + message)


def get_original(gid):
    norm = read(
        DATA / "b1_normalized_v11" / "games"
        / gid / "normalized_game.json"
    )
    sel = read(
        DATA / "b1_selection_v1" / "games" / f"{gid}.json"
    )
    return norm, sel


def get_overlay(gid):
    norm = read(
        OVERLAY / "b1_normalized_v11" / "games"
        / gid / "normalized_game.json"
    )
    sel = read(
        OVERLAY / "b1_selection_v1" / "games" / f"{gid}.json"
    )
    return norm, sel


def find_one(game, seq, description, inning, half):
    matched = [
        p for p in game["plays"]
        if p["source_seqno"] == seq
        and p["description"] == description
        and p["inning"] == inning
        and p["inning_half"] == half
    ]
    check(len(matched) == 1, f"Missing/duplicate source row {seq}")
    return matched[0]["play_id"]


def main():
    normal_dir = DATA / "b1_normalized_v11" / "games"
    selected_dir = DATA / "b1_selection_v1" / "games"

    check(
        len(list(normal_dir.glob("*/normalized_game.json"))) == 720,
        "Original normalized game count is not 720"
    )
    check(
        len(list(selected_dir.glob("*.json"))) == 720,
        "Original selection game count is not 720"
    )

    check(
        read(DATA / "b1_normalized_v11" / "run_report.json")
        ["status"] == "STRUCTURAL_PASS",
        "Original normalization report is not PASS"
    )
    check(
        read(DATA / "b1_selection_v1" / "finish_report.json")
        ["status"] == "SELECTION_PASS_WITH_LIMITATIONS",
        "Original selection report is not PASS"
    )
    print("[PASS] Original 720-game B1 controls")

    for gid, delta, added_count in [
        (A, 6, 6), (B, -1, 0), (C, 1, 1)
    ]:
        original, orig_sel = get_original(gid)
        changed, new_sel = get_overlay(gid)

        old_by_id = {p["play_id"]: p for p in original["plays"]}
        new_by_id = {p["play_id"]: p for p in changed["plays"]}

        check(
            len(old_by_id) == len(original["plays"]),
            f"{gid}: duplicate original IDs"
        )
        check(
            len(new_by_id) == len(changed["plays"]),
            f"{gid}: duplicate corrected IDs"
        )
        check(
            all(new_by_id.get(pid) == p
                for pid, p in old_by_id.items()),
            f"{gid}: original play changed or disappeared"
        )
        check(
            changed["tracking_records"] ==
            original["tracking_records"],
            f"{gid}: original tracking data changed"
        )

        added = [
            p for pid, p in new_by_id.items()
            if pid not in old_by_id
        ]
        check(
            len(added) == added_count,
            f"{gid}: incorrect manual row count"
        )

        for p in added:
            check(
                p["record_unit"] ==
                "manual_verified_reconstruction",
                f"{gid}: missing manual provenance"
            )
            check(
                p["source_seqno"] is None,
                f"{gid}: invented original seqno"
            )
            check(
                "manual_source_reconstruction"
                in p["review_flags"],
                f"{gid}: missing review flag"
            )
            if p["event_type"] == "pitch":
                pitch = p["pitch"]
                check(
                    pitch["source_pitch_id"] is None
                    and pitch["tracking_id"] is None
                    and pitch["speed_value"] is None,
                    f"{gid}: unverified physical pitch data"
                )

        old_order = orig_sel["ordered_play_ids"]
        new_order = new_sel["ordered_play_ids"]

        check(
            len(new_order) - len(old_order) == delta,
            f"{gid}: incorrect selected row difference"
        )
        check(
            len(new_order) == len(set(new_order)),
            f"{gid}: duplicate selected IDs"
        )
        check(
            all(pid in new_by_id for pid in new_order),
            f"{gid}: dangling selected ID"
        )

        print(f"[PASS] {gid}: selected delta {delta:+d}")

    # Case 2: the incorrect row must be excluded, not deleted.
    original_b, old_sel_b = get_original(B)
    changed_b, new_sel_b = get_overlay(B)
    bad_id = find_one(
        original_b, 328,
        "2루주자 문성주 : 3루까지 진루",
        5, "bottom"
    )
    check(
        bad_id in {p["play_id"] for p in changed_b["plays"]},
        "Case 2: original row was deleted"
    )
    check(
        bad_id in old_sel_b["ordered_play_ids"]
        and bad_id not in new_sel_b["ordered_play_ids"],
        "Case 2: incorrect advance was not excluded"
    )
    print("[PASS] Case 2: invalid advance excluded")

    # Case 4: both records at each colliding seqno survive.
    game_d, sel_d = get_original(D)
    pairs = [
        (375, "추재현 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)", 7, "bottom"),
        (375, "8회초 KIA 공격", 8, "top"),
        (398, "박정우 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)", 8, "top"),
        (398, "8회말 키움 공격", 8, "bottom"),
    ]
    for seq, desc, inning, half in pairs:
        pid = find_one(game_d, seq, desc, inning, half)
        check(
            pid in sel_d["ordered_play_ids"],
            f"Case 4: missing selected record {desc}"
        )
    print("[PASS] Case 4: both seqno collisions preserved")

    print()
    print("B1 V2 PREFLIGHT PASS")
    print("Original normalized rows and tracking preserved")
    print("Expected selected row net change: +6")
    print("B2 state and B3 integration still require validation")


if __name__ == "__main__":
    main()
