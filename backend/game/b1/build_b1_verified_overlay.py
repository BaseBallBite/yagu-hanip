
"""Create a 3-game verified B1 overlay for B2 regression testing.

Original raw and B1 outputs remain unchanged.
This is NOT a replacement for the original full B1 contract.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from normalize_b1 import classify, stable_id, TEAMS
from b1_selection_core import CONTEXT, NOTICES, ADMIN

A = "20260415WOHT02026"
B = "20260401HTLG02026"
C = "20260415SSHH02026"
D = "20260822HTWO02026"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_row(game, seq, text, inning, half):
    matches = [
        p for p in game["plays"]
        if p.get("source_seqno") == seq
        and p["description"] == text
        and p["inning"] == inning
        and p["inning_half"] == half
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{game['game_id']}: expected one source row "
            f"{seq} {text}, found {len(matches)}"
        )
    return matches[0]


def new_rows(game, case, case_name):
    gid = game["game_id"]
    meta = game.get("metadata_raw") or {}
    half = case["half"]
    batting = meta.get("awayTeamCode") if half == "top" else meta.get("homeTeamCode")
    fielding = meta.get("homeTeamCode") if half == "top" else meta.get("awayTeamCode")

    result = []
    for n, text in enumerate(case["records"], 1):
        event, tags, rule = classify(text, {})
        if event == "unknown":
            raise ValueError(f"Cannot classify manual row: {text}")

        ref = f"{gid}/manual_verified/{case_name}/{n:02d}"
        pitch = None

        if event == "pitch":
            match = re.match(r"^(\d+)구\s+(.+)$", text)
            if not match:
                raise ValueError("Invalid manual pitch: " + text)
            pitch = {
                "pitch_id": stable_id(gid, "pitch", ref),
                "pitch_number": int(match.group(1)),
                "pitch_type": None,
                "pitch_type_raw": None,
                "speed_value": None,
                "speed_unit": None,
                "result_text": match.group(2),
                "result_code_raw": None,
                "source_pitch_id": None,
                "tracking_id": None,
                "tracking_candidate_ids": [],
                "tracking_status": "source_id_missing",
                "same_id_candidate_ids": [],
                "link_basis": None,
            }

        result.append({
            "play_id": stable_id(gid, "play", ref),
            "play_number": None,
            "game_id": gid,
            "record_unit": "manual_verified_reconstruction",
            "plate_appearance_id": None,
            "inning": case["inning"],
            "inning_half": half,
            "batter": None,
            "pitcher": None,
            "batting_team_id": TEAMS.get(batting),
            "fielding_team_id": TEAMS.get(fielding),
            "event_type": event,
            "event_tags": tags,
            "classification_rule": rule,
            "classification_status": "manual_review",
            "description": text,
            "source_seqno": None,
            "outs_before": None,
            "outs_after": None,
            "score_before": None,
            "score_after": None,
            "runners_before": None,
            "runners_after": None,
            "state_status": "pending_B2",
            "pitch": pitch,
            "review_flags": ["manual_source_reconstruction"],
            "source_record": {
                "game_id": gid,
                "source_ref": ref,
                "source_file": "manual_verified_overlay",
                "inning": case["inning"],
                "half_raw": "0" if half == "top" else "1",
                "seqno": None,
                "text": text,
                "raw": {"text": text, "seqno": None},
                "verification_provenance": case.get("evidence")
            }
        })

    return result


def refresh_selection(game, selection):
    by_id = {p["play_id"]: p for p in game["plays"]}
    ordered = selection["ordered_play_ids"]

    if len(by_id) != len(game["plays"]):
        raise ValueError("Duplicate play_id")
    if len(ordered) != len(set(ordered)):
        raise ValueError("Duplicate selected play_id")
    if not set(ordered).issubset(by_id):
        raise ValueError("Selected play_id missing from normalized data")

    selection["context_ids"] = [
        pid for pid in ordered
        if by_id[pid]["event_type"] in CONTEXT
    ]
    selection["notice_ids"] = [
        pid for pid in ordered
        if by_id[pid]["event_type"] in NOTICES
    ]
    selection["event_candidate_ids"] = [
        pid for pid in ordered
        if by_id[pid]["event_type"] not in CONTEXT | NOTICES | ADMIN
    ]
    selection["text_rows_accounted_for"] = len(game["plays"])
    selection["state_reconstruction_complete"] = False
    selection["semantic_review_complete"] = False
    selection["status"] = "MANUAL_OVERLAY_READY_FOR_B2_TEST"

    for pid in ordered:
        p = by_id[pid]
        if p["record_unit"] == "manual_verified_reconstruction":
            if not any(
                r["play_id"] == pid
                for r in selection["pending_semantics"]
            ):
                selection["pending_semantics"].append({
                    "play_id": pid,
                    "event_type": p["event_type"],
                    "flags": ["manual_source_reconstruction"]
                })

    return game, selection


def apply(game, selection, case):
    gid = game["game_id"]
    if selection["game_id"] != gid:
        raise ValueError("Game ID mismatch")

    game = copy.deepcopy(game)
    selection = copy.deepcopy(selection)
    ordered = selection["ordered_play_ids"]

    if gid == A:
        anchor = source_row(
            game, 6, "2번타자 안치홍", 1, "top"
        )
        if len(case["records"]) != 6:
            raise ValueError("Case A must contain six rows")
        if any(
            p["inning"] == 1
            and p["inning_half"] == "top"
            and p["event_type"] == "inning_start"
            for p in game["plays"]
        ):
            raise ValueError("First-inning header already exists")

        additions = new_rows(game, case, "missing_first_pa")
        pi = game["plays"].index(anchor)
        si = ordered.index(anchor["play_id"])
        game["plays"][pi:pi] = additions
        ordered[si:si] = [p["play_id"] for p in additions]

    elif gid == B:
        source_row(
            game, 327,
            "오지환 : 1루수 땅볼 아웃 (1루수 1루 터치아웃)",
            5, "bottom"
        )
        bad = source_row(
            game, 328,
            "2루주자 문성주 : 3루까지 진루",
            5, "bottom"
        )
        ordered.remove(bad["play_id"])
        selection["excluded_from_sequence"].append({
            "play_id": bad["play_id"],
            "action": "verified_incorrect_runner_advance",
            "replacement_play_id": None,
            "reason": "Video shows runners remain on second and third"
        })

    elif gid == C:
        anchor = source_row(
            game, 597, "류지혁 : 볼넷", 8, "top"
        )
        next_row = source_row(
            game, 598, "6번타자 박세혁", 8, "top"
        )
        si = ordered.index(anchor["play_id"])
        if ordered[si + 1] != next_row["play_id"]:
            raise ValueError("Unexpected event between 597 and 598")
        additions = new_rows(game, case, "forced_runner_advance")
        if len(additions) != 1:
            raise ValueError("Case C must contain one row")
        pi = game["plays"].index(anchor)
        game["plays"][pi + 1:pi + 1] = additions
        ordered[si + 1:si + 1] = [p["play_id"] for p in additions]

    return refresh_selection(game, selection)


def check_case_d(game, selection):
    checks = [
        (375, "추재현 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)", 7, "bottom"),
        (375, "8회초 KIA 공격", 8, "top"),
        (398, "박정우 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)", 8, "top"),
        (398, "8회말 키움 공격", 8, "bottom")
    ]
    for seq, text, inn, half in checks:
        p = source_row(game, seq, text, inn, half)
        if p["play_id"] not in selection["ordered_play_ids"]:
            raise ValueError("B1 selection lost collision row: " + text)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--b1-root", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.b1_root.resolve()
    out = args.out.resolve()
    if out.exists():
        raise ValueError("Output exists. Choose a NEW folder.")
    if out == root or root in out.parents or out in root.parents:
        raise ValueError("Output must be outside the B1 input folder")

    rules = read(args.rules)
    cases = {c["game_id"]: c for c in rules["cases"]}
    if set(cases) != {A, B, C, D}:
        raise ValueError("Unexpected correction cases")

    results = {}
    fingerprints = {}

    # Validate everything before writing any output.
    for gid in (A, B, C, D):
        np = root / "b1_normalized_v11" / "games" / gid / "normalized_game.json"
        sp = root / "b1_selection_v1" / "games" / f"{gid}.json"
        if not np.is_file() or not sp.is_file():
            raise FileNotFoundError(
                f"Missing B1 files for {gid}. Check --b1-root: {root}"
            )
        fingerprints[str(np)] = sha(np)
        fingerprints[str(sp)] = sha(sp)

        original = read(np)
        original_sel = read(sp)
        if gid == D:
            check_case_d(original, original_sel)
            print(gid, "COLLISION RECORDS PRESERVED")
            continue

        patched, selected = apply(original, original_sel, cases[gid])
        expected = {A: 6, B: -1, C: 1}[gid]
        delta = (
            len(selected["ordered_play_ids"])
            - len(original_sel["ordered_play_ids"])
        )
        if delta != expected:
            raise ValueError(f"Unexpected selected row delta: {gid} {delta}")

        # No original normalized row may be deleted or modified.
        new_by_id = {p["play_id"]: p for p in patched["plays"]}
        for p in original["plays"]:
            if new_by_id.get(p["play_id"]) != p:
                raise ValueError("Original normalized play changed")

        results[gid] = (patched, selected)
        print(gid, "OVERLAY VERIFIED", f"selected_delta={delta:+d}")

    if any(sha(Path(path)) != value for path, value in fingerprints.items()):
        raise ValueError("B1 inputs changed during validation")

    tmp = out.with_name(out.name + ".tmp")
    if tmp.exists():
        raise ValueError("Temporary output already exists: " + str(tmp))
    tmp.mkdir(parents=True)

    for gid, (normalized, selected) in results.items():
        write(
            tmp / "b1_normalized_v11" / "games" / gid / "normalized_game.json",
            normalized
        )
        write(
            tmp / "b1_selection_v1" / "games" / f"{gid}.json",
            selected
        )

    write(tmp / "overlay_report.json", {
        "status": "READY_FOR_THREE_GAME_B2_TEST",
        "corrected_games": [A, B, C],
        "verified_unchanged_game": D,
        "selected_row_changes": {A: 6, B: -1, C: 1},
        "originals_modified": False,
        "original_input_sha256": fingerprints,
        "note": (
            "Three-game B2 testing overlay only. "
            "Not a complete 720-game B1 handoff or a certified B1 structural pass."
        )
    })
    tmp.rename(out)
    print("OUTPUT:", out)
    print("ORIGINAL B1 FILES UNCHANGED")


if __name__ == "__main__":
    main()
