
"""Build and verify a 720-game corrected B1 package."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from b1_selection_core import select_game
from build_b1_handoff import build_game
from build_b1_plate_appearances import group_game


CHANGES = {
    "20260415WOHT02026": (6, 6),
    "20260401HTLG02026": (0, -1),
    "20260415SSHH02026": (1, 1),
}
COLLISION_GAME = "20260822HTWO02026"
ROOT_IN_ZIP = "B1_corrected_v2/data"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(z, name, value):
    content = json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False
    )
    z.writestr(name, content.encode("utf-8"))


def check_selection(data, selection, gid):
    require(data["game_id"] == gid, f"{gid}: wrong game")
    require(selection["game_id"] == gid, f"{gid}: wrong selection game")
    expected_status = (
        "MANUAL_OVERLAY_READY_FOR_B2_TEST"
        if gid in CHANGES
        else "SELECTION_CHECKS_PASS"
    )
    require(
        selection.get("status") == expected_status,
        f"{gid}: unexpected selection status",
    )
    require(
        not selection.get("blocking_issues"),
        f"{gid}: unresolved blocking issues",
    )

    category_ids = (
        selection.get("event_candidate_ids", [])
        + selection.get("context_ids", [])
        + selection.get("notice_ids", [])
    )
    require(
        len(category_ids) == len(selection["ordered_play_ids"])
        and len(set(category_ids)) == len(category_ids)
        and set(category_ids) == set(selection["ordered_play_ids"]),
        f"{gid}: category coverage mismatch",
    )
    require(
        selection.get("text_rows_accounted_for") == len(data["plays"]),
        f"{gid}: text row coverage mismatch",
    )

    all_ids = [p["play_id"] for p in data["plays"]]
    chosen = selection["ordered_play_ids"]
    excluded = [
        row["play_id"]
        for row in selection["excluded_from_sequence"]
    ]

    require(len(all_ids) == len(set(all_ids)), f"{gid}: duplicate plays")
    require(len(chosen) == len(set(chosen)), f"{gid}: duplicate selection")
    require(
        len(chosen) + len(excluded) == len(all_ids),
        f"{gid}: row coverage mismatch",
    )
    require(
        set(chosen).isdisjoint(excluded)
        and set(chosen) | set(excluded) == set(all_ids),
        f"{gid}: lost or duplicated selection rows",
    )

    track_ids = [x["tracking_id"] for x in data["tracking_records"]]
    require(
        len(track_ids) == len(set(track_ids)),
        f"{gid}: duplicate tracking IDs",
    )


def validate_changed(gid, original, patched, old_sel, new_sel):
    extra, delta = CHANGES[gid]

    original_plays = original["plays"]
    patched_plays = patched["plays"]

    require(
        len(patched_plays) == len(original_plays) + extra,
        f"{gid}: wrong number of added rows",
    )
    require(
        len(new_sel["ordered_play_ids"])
        == len(old_sel["ordered_play_ids"]) + delta,
        f"{gid}: incorrect selected row delta",
    )

    original_refs = {
        p["source_record"]["source_ref"]: p for p in original_plays
    }
    retained = [
        p for p in patched_plays
        if p["source_record"]["source_ref"] in original_refs
    ]

    require(
        [p["play_id"] for p in retained]
        == [p["play_id"] for p in original_plays],
        f"{gid}: original play IDs/order changed",
    )
    require(
        [p["source_record"] for p in retained]
        == [p["source_record"] for p in original_plays],
        f"{gid}: original source rows changed",
    )
    require(
        patched["tracking_records"] == original["tracking_records"],
        f"{gid}: original tracking data changed",
    )

    added = [
        p for p in patched_plays
        if p["source_record"]["source_ref"] not in original_refs
    ]
    require(len(added) == extra, f"{gid}: added row mismatch")

    selected = set(new_sel["ordered_play_ids"])
    require(
        all(p["play_id"] in selected for p in added),
        f"{gid}: manual rows not selected",
    )

    if gid == "20260415WOHT02026":
        expected = [
            "1회초 키움 공격",
            "1번타자 이주형",
            "1구 스트라이크",
            "2구 볼",
            "3구 타격",
            "이주형 : 좌익수 앞 1루타",
        ]
        require(
            [p["description"] for p in added] == expected,
            "Case 1: manual text differs from approved correction",
        )
        pitches = [p for p in added if p["event_type"] == "pitch"]
        require(len(pitches) == 3, "Case 1: expected three pitch rows")
        for p in pitches:
            pitch = p.get("pitch") or {}
            require(
                pitch.get("source_pitch_id") is None
                and pitch.get("tracking_id") is None
                and pitch.get("tracking_status") == "source_id_missing",
                "Case 1: invented source pitch/tracking information",
            )

    if gid == "20260401HTLG02026":
        errors = [
            p for p in original_plays
            if str(p["source_seqno"]) == "328"
            and "문성주" in p["description"]
            and "3루까지 진루" in p["description"]
        ]
        require(len(errors) == 1, "Case 2: seqno 328 not identified")
        bad = errors[0]["play_id"]
        excluded = {
            x["play_id"] for x in new_sel["excluded_from_sequence"]
        }
        require(
            bad in excluded and bad not in selected,
            "Case 2: invalid runner advance still selected",
        )

    if gid == "20260415SSHH02026":
        require(
            len(added) == 1 and
            added[0]["description"] ==
            "1루주자 김재상 : 2루까지 진루",
            "Case 3: incorrect manual runner advance",
        )
        order = new_sel["ordered_play_ids"]
        by_seq = {
            str(p["source_seqno"]): p["play_id"]
            for p in original_plays
        }
        require(
            order.index(by_seq["597"])
            < order.index(added[0]["play_id"])
            < order.index(by_seq["598"]),
            "Case 3: incorrect insertion position",
        )


def validate_collision(data, selection):
    selected = set(selection["ordered_play_ids"])
    for number in (375, 398):
        rows = [
            p for p in data["plays"]
            if str(p["source_seqno"]) == str(number)
        ]
        require(
            len(rows) == 2,
            f"Case 4: seqno {number} must have two rows",
        )
        require(
            all(p["play_id"] in selected for p in rows),
            f"Case 4: seqno {number} record lost",
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument(
        "--base", type=Path,
        default=Path("data/b1_normalized_v2_base"),
    )
    ap.add_argument(
        "--overlay", type=Path,
        default=Path("b1_verified_overlay_v1"),
    )
    ap.add_argument(
        "--rules", type=Path, default=Path("selection_rules.json"),
    )
    ap.add_argument(
        "--corrections", type=Path,
        default=Path("b1_manual_corrections_v1.json"),
    )
    ap.add_argument(
        "--out", type=Path, default=Path("B1_corrected_v2.zip"),
    )
    args = ap.parse_args()

    base = args.base.resolve()
    data_root = args.data.resolve()
    overlay = args.overlay.resolve()
    out = args.out.resolve()
    temp = Path(str(out) + ".partial")

    require(not out.exists(), f"Output already exists: {out}")
    require(not temp.exists(), f"Partial output exists: {temp}")
    require(args.rules.is_file(), "selection_rules.json missing")
    require(args.corrections.is_file(), "manual corrections missing")

    original_root = data_root / "b1_normalized_v11" / "games"
    selected_root = data_root / "b1_selection_v1" / "games"
    new_root = base / "games"
    patched_root = overlay / "b1_normalized_v11" / "games"
    patched_selection = overlay / "b1_selection_v1" / "games"

    report = read(base / "run_report.json")
    require(report["status"] == "STRUCTURAL_PASS", "Base not passed")
    require(report["normalized_games"] == 720, "Not 720 games")
    require(report["failed_games"] == 0, "Failed normalization")

    game_ids = sorted(
        p.name for p in new_root.iterdir() if p.is_dir()
    )
    require(len(game_ids) == 720, "Incorrect number of game folders")
    require(
        all(gid in game_ids for gid in (*CHANGES, COLLISION_GAME)),
        "One or more reviewed games missing",
    )

    rules = read(args.rules)
    plans = {g["game_id"]: g for g in rules["games"]}
    totals = {
        "original_text_rows": 0,
        "corrected_text_rows": 0,
        "original_selected_rows": 0,
        "corrected_selected_rows": 0,
        "tracking_rows": 0,
    }
    changed_games = []

    b2_review = {
        "20260401HTLG02026": {
            "after_seqno": 327,
            "expected_outs": 2,
            "expected_runners": {
                "1": None, "2": "문성주", "3": "박동원"
            },
            "expected_score_delta": 0,
            "note": "Keep original source; exclude invalid seqno 328 from selected timeline.",
        },
        "20260415SSHH02026": {
            "after_event": "류지혁 : 볼넷",
            "expected_outs": 2,
            "expected_runners": {
                "1": "류지혁", "2": "김재상", "3": "박승규"
            },
            "note": "Forced advance; verify B2 handles runner movement without double counting.",
        },
        "20260415WOHT02026": {
            "note": "Six manually restored rows. First two pitch order is based on supplied review; no original pitch tracking IDs.",
        },
        "20260822HTWO02026": {
            "note": "Preserve both distinct records for each duplicated seqno 375 and 398.",
        },
    }

    try:
        with ZipFile(
            temp, "w", compression=ZIP_DEFLATED, compresslevel=3,
            allowZip64=True,
        ) as z:
            for n, gid in enumerate(game_ids, 1):
                baseline_path = new_root / gid / "normalized_game.json"
                previous_path = (
                    original_root / gid / "normalized_game.json"
                )
                previous_selection_path = (
                    selected_root / (gid + ".json")
                )

                baseline_hash = sha256(baseline_path)
                require(
                    baseline_hash == sha256(previous_path),
                    f"{gid}: regenerated B1 differs from original",
                )

                baseline = read(baseline_path)
                previous_sel = read(previous_selection_path)

                if gid in CHANGES:
                    normalized_path = (
                        patched_root / gid / "normalized_game.json"
                    )
                    selection_path = (
                        patched_selection / (gid + ".json")
                    )
                    normalized = read(normalized_path)
                    selection = read(selection_path)
                    validate_changed(
                        gid, baseline, normalized,
                        previous_sel, selection,
                    )
                    changed_games.append(gid)
                else:
                    normalized_path = baseline_path
                    selection_path = previous_selection_path
                    normalized = baseline
                    selection = previous_sel

                    reproduced = select_game(
                        baseline, plans.get(gid)
                    )
                    reproduced["normalized_file_sha256"] = baseline_hash
                    require(
                        reproduced == selection,
                        f"{gid}: original selection not reproducible",
                    )

                actual_hash = sha256(normalized_path)

                if gid in CHANGES:
                    require(
                        selection.get("normalized_file_sha256") == baseline_hash,
                        f"{gid}: unexpected original hash",
                    )
                    selection = dict(selection)
                    selection["normalized_file_sha256"] = actual_hash

                require(
                    selection.get("normalized_file_sha256") == actual_hash,
                    f"{gid}: normalized/selection hash mismatch",
                )
                check_selection(normalized, selection, gid)

                if gid == COLLISION_GAME:
                    validate_collision(normalized, selection)

                handoff = build_game(normalized, selection)
                pa = group_game(normalized, selection)

                require(
                    len(handoff["records"])
                    == len(selection["ordered_play_ids"]),
                    f"{gid}: handoff coverage mismatch",
                )
                require(
                    len(pa["row_links"])
                    == len(selection["ordered_play_ids"]),
                    f"{gid}: plate-appearance coverage mismatch",
                )

                totals["original_text_rows"] += len(baseline["plays"])
                totals["corrected_text_rows"] += len(normalized["plays"])
                totals["original_selected_rows"] += len(
                    previous_sel["ordered_play_ids"]
                )
                totals["corrected_selected_rows"] += len(
                    selection["ordered_play_ids"]
                )
                totals["tracking_rows"] += len(
                    normalized["tracking_records"]
                )

                prefix = ROOT_IN_ZIP
                z.write(
                    normalized_path,
                    f"{prefix}/b1_normalized_v11/games/{gid}/normalized_game.json",
                )
                if gid in CHANGES:
                    write_json(
                        z,
                        f"{prefix}/b1_selection_v1/games/{gid}.json",
                        selection,
                    )
                else:
                    z.write(
                        selection_path,
                        f"{prefix}/b1_selection_v1/games/{gid}.json",
                    )
                write_json(
                    z, f"{prefix}/b1_handoff_v2/games/{gid}.json",
                    handoff,
                )
                write_json(
                    z,
                    f"{prefix}/b1_plate_appearances_v2/games/{gid}.json",
                    pa,
                )

                if n % 50 == 0 or n == 720:
                    print(f"[{n}/720] VALIDATED AND PACKAGED", flush=True)

            require(
                totals["original_text_rows"] == 401864,
                "Original text row total changed",
            )
            require(
                totals["corrected_text_rows"] == 401871,
                "Expected seven manually added rows",
            )
            require(
                totals["tracking_rows"] == 221480,
                "Tracking rows changed",
            )
            require(
                totals["corrected_selected_rows"]
                - totals["original_selected_rows"] == 6,
                "Selected row net change is not +6",
            )
            require(
                set(changed_games) == set(CHANGES),
                "Incorrect corrected-game coverage",
            )

            validation = {
                "status": "B1_V2_PACKAGE_STRUCTURAL_PASS",
                "total_games": 720,
                "patched_games": changed_games,
                "unchanged_games": 717,
                "totals": totals,
                "original_normalization_reproduced": True,
                "source_tracking_preserved": True,
                "b2_state_validation_complete": False,
                "b3_integration_complete": False,
                "note": (
                    "This package uses regenerated B1 as its base, "
                    "three verified overlays, and retained source IDs. "
                    "B2 must independently verify runner identities and states."
                ),
            }
            write_json(
                z, f"{ROOT_IN_ZIP}/validation_report_v2.json",
                validation,
            )
            write_json(
                z, f"{ROOT_IN_ZIP}/b2_review_cases_v2.json",
                b2_review,
            )

        with ZipFile(temp, "r") as z:
            require(
                len(z.namelist()) == 720 * 4 + 2,
                "ZIP member count mismatch",
            )
            require(z.testzip() is None, "ZIP CRC integrity failed")

        os.replace(temp, out)
        print("\nB1 V2 PACKAGE CREATED")
        print("720 games included")
        print("Original records and tracking preserved")
        print("7 manual rows added; 1 original row excluded from selection")
        print("ZIP integrity PASS")
        print("OUTPUT:", out)
        print("B2/B3 validation still required")

    except Exception:
        if temp.exists():
            temp.unlink()
        raise


if __name__ == "__main__":
    main()
