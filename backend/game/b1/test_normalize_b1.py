import argparse
import contextlib
import copy
import csv
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
import normalize_b1 as n


def row(ref='r1', text='A : 볼넷', seq=1, game='game1', half='0', pitch_id=None):
    raw = {'seqno': seq, 'text': text, 'currentGameState': {'batter': '10', 'pitcher': '20', 'base1': '0'}}
    if pitch_id is not None:
        raw['ptsPitchId'] = pitch_id
    return {'game_id': game, 'source_ref': ref, 'inning': 1, 'half_raw': half,
            'source_file': 'inning_01.json', 'block_index': 0,
            'relay_no': 1, 'seqno': seq, 'text': text, 'raw': raw}


def track(ref='p1', game='game1', pitch_id='p', half='0'):
    return {'game_id': game, 'source_ref': ref, 'inning': 1, 'half_raw': half,
            'source_file': 'inning_01.json', 'block_index': 0,
            'relay_no': 1, 'raw': {'pitchId': pitch_id, 'crossPlateX': .2, 'new_field': {'a': 1}}}


def write_input(root, game='game1', texts=None, pitches=None):
    folder = root / game
    folder.mkdir(parents=True)
    for name, rows in [('text_rows.jsonl', texts if texts is not None else [row(game=game)]),
                       ('pitch_rows.jsonl', pitches or [])]:
        (folder / name).write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows), encoding='utf-8')
    return folder


class Core(unittest.TestCase):
    def test_full_raw_preservation(self):
        r = row(); r['raw']['future_field'] = {'list': [1, None, False, '한글']}
        before = copy.deepcopy(r)
        out, report, _, _ = n.normalize_game([r], [track()])
        self.assertEqual(out['plays'][0]['source_record'], before)
        self.assertEqual(r, before)
        self.assertTrue(report['source_records_preserved'])

    def test_duplicate_seq_all_preserved(self):
        rows = [row('a', 'A : 대타 B (으)로 교체'), row('b', '대타 B')]
        out, _, c, _ = n.normalize_game(rows, [])
        self.assertEqual(len(out['plays']), 2)
        self.assertEqual(c[0]['classification'], 'distinct_records_same_seqno')
        self.assertEqual(len({x['play_id'] for x in out['plays']}), 2)

    def test_exact_repeat_not_deleted(self):
        a, b = row('a'), row('b')
        out, _, c, _ = n.normalize_game([a, b], [])
        self.assertEqual(len(out['plays']), 2)
        self.assertEqual(c[0]['classification'], 'exact_payload_repeat_candidate')
        self.assertTrue(c[0]['review_required'])

    def test_same_text_different_state(self):
        a, b = row('a'), row('b'); b['raw']['currentGameState']['base1'] = '1'
        _, _, c, _ = n.normalize_game([a, b], [])
        self.assertEqual(c[0]['classification'], 'same_text_different_payload')

    def test_correction_not_overwrite(self):
        out, _, c, _ = n.normalize_game([row('a', 'A : 홈런'), row('b', 'A : 홈런 취소')], [])
        self.assertEqual(len(out['plays']), 2)
        self.assertEqual(c[0]['classification'], 'correction_candidate')

    def test_ids_stable_on_input_reordering(self):
        rows = [row('a', seq=1), row('b', seq=2)]
        first = n.normalize_game(rows, [])[0]['plays']
        second = n.normalize_game(rows[::-1], [])[0]['plays']
        self.assertEqual(first[0]['play_id'], second[1]['play_id'])

    def test_id_namespace_per_game(self):
        a = n.normalize_game([row()], [])[0]['plays'][0]['play_id']
        b = n.normalize_game([row(game='other')], [])[0]['plays'][0]['play_id']
        self.assertNotEqual(a, b)

    def test_duplicate_source_ref_rejected(self):
        with self.assertRaises(ValueError): n.normalize_game([row(), row()], [])

    def test_mixed_game_rejected(self):
        with self.assertRaises(ValueError): n.normalize_game([row()], [track(game='other')])

    def test_exact_pitch_join(self):
        out = n.normalize_game([row(text='1구 볼', pitch_id='p')], [track()])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'matched')

    def test_sentinel_minus_one_never_joins(self):
        out = n.normalize_game([row(text='1구 헛스윙', pitch_id='-1')], [track(pitch_id='-1')])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'source_id_missing')
        self.assertIsNone(out['plays'][0]['pitch']['tracking_id'])

    def test_many_tracking_candidates_not_joined(self):
        out = n.normalize_game([row(text='1구 볼', pitch_id='p')], [track('p1'), track('p2')])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'ambiguous')

    def test_reused_text_pitch_id_not_joined(self):
        rows = [row('a', '1구 볼', pitch_id='p'), row('b', '2구 볼', 2, pitch_id='p')]
        out = n.normalize_game(rows, [track()])[0]
        self.assertTrue(all(p['pitch']['tracking_status'] == 'ambiguous' for p in out['plays']))

    def test_cross_half_join_blocked(self):
        out = n.normalize_game([row(text='1구 볼', pitch_id='p')], [track(half='1')])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'context_conflict')

    def test_repeated_id_different_blocks_link_but_not_deduplicated(self):
        a, b = row('a', '1구 볼', pitch_id='p'), row('b', '1구 볼', pitch_id='p')
        b['block_index'] = 1
        b['raw']['currentGameState']['homeHit'] = '12'
        x, y = track('x'), track('y'); y['block_index'] = 1
        out, report, _, issues = n.normalize_game([a,b], [x,y])
        self.assertEqual(report['pitch_links'], {'matched': 2})
        self.assertEqual(len(out['plays']), 2)
        self.assertEqual(len({p['pitch']['tracking_id'] for p in out['plays']}), 2)
        group = out['repeat_candidate_groups'][0]
        self.assertIn('homeHit', group['differing_state_fields'])
        self.assertIsNone(group['canonical_play_id'])
        self.assertTrue(out['timeline_review_required'])
        self.assertTrue(all('repeated_pitch_id_review' in p['review_flags'] for p in out['plays']))
        self.assertNotIn('unlinked_tracking', [i['code'] for i in issues])

    def test_same_relay_other_source_block_not_joined(self):
        t = track(); t['block_index'] = 1
        out = n.normalize_game([row(text='1구 볼', pitch_id='p')], [t])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'context_conflict')

    def test_missing_block_no_global_fallback(self):
        r = row(text='1구 볼', pitch_id='p'); del r['block_index']
        out = n.normalize_game([r], [track()])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'source_context_missing')

    def test_pitch_number_conflict_not_joined(self):
        r = row(text='1구 볼', pitch_id='p'); r['raw']['pitchNum'] = 1
        t = track(); t['raw']['ballcount'] = 2
        out = n.normalize_game([r], [t])[0]
        self.assertEqual(out['plays'][0]['pitch']['tracking_status'], 'context_conflict')

    def test_explicit_outcomes_and_notice_guard(self):
        cases = {
            'A : 포수 스트라이크 낫 아웃 (포수 태그아웃)': 'dropped_third_strike',
            'A : 투수 앞 번트안타': 'single',
            'A : 3루수 번트 아웃': 'bunt_out',
            'A : 쓰리번트 아웃': 'strikeout',
            'A : 타구맞음 아웃': 'batted_ball_out',
            '3회초 1번타순 2구 체크스윙 → 스윙 : A': 'check_swing_notice',
            '3회초 1번타순 2구 후 최초 직선타 형태 병살타 인정 안됨': 'play_notice',
            '4회초 2번타순 초구 전 2분간 폭염 관련 쿨링 브레이크 추가': 'break_notice',
            '1회초 1번타순 2구 후 ABS 추적 실패로 심판 자체 판정: 볼': 'abs_notice',
            '무승부팀 홀드투수: A': 'game_result_notice'}
        for text, expected in cases.items():
            with self.subTest(text=text): self.assertEqual(n.classify(text, {})[0], expected)

    def test_unknown_half_not_bottom(self):
        out, _, _, issues = n.normalize_game([row(half='2')], [])
        self.assertIsNone(out['plays'][0]['inning_half'])
        self.assertIn('unknown_half', [i['code'] for i in issues])

    def test_before_after_stay_unknown(self):
        p = n.normalize_game([row()], [])[0]['plays'][0]
        for name in ['outs_before', 'outs_after', 'runners_before', 'runners_after', 'score_before', 'score_after']:
            self.assertIsNone(p[name])

    def test_name_join_requires_same_player_id(self):
        r = row(); r['raw']['batterRecord'] = {'pcode': '999', 'name': '다른선수'}
        p = n.normalize_game([r], [])[0]['plays'][0]
        self.assertIsNone(p['batter']['name'])

    def test_sort_decrease_is_reviewed_not_silently_sorted(self):
        out, _, _, issues = n.normalize_game([row('a', seq=2), row('b', seq=1)], [])
        self.assertEqual(out['plays'][0]['source_seqno'], 2)
        self.assertIn('source_order_decrease', [i['code'] for i in issues])

    def test_classifier_distinguishes_runner(self):
        self.assertEqual(n.classify('1루주자 A : 도루로 2루까지 진루', {})[0], 'steal')
        self.assertEqual(n.classify('3루주자 A : 폭투로 홈인', {})[0], 'run_scored')
        self.assertIn('wild_pitch', n.classify('3루주자 A : 폭투로 홈인', {})[1])

    def test_no_fielders_choice_guess(self):
        self.assertEqual(n.classify('A : 유격수 앞 땅볼로 출루', {})[0], 'reach_unspecified')

    def test_review_sentence_is_not_a_hit(self):
        self.assertEqual(n.classify('비디오 판독: A 홈런→2루타', {})[0], 'video_review')
        self.assertEqual(n.classify('A : 홈런성 타구', {})[0], 'unknown')

    def test_bom_and_malformed_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'x.jsonl'; p.write_text('\ufeff'+json.dumps(row())+'\n', encoding='utf-8')
            self.assertEqual(len(n.load_jsonl(p)), 1)
            p.write_text('{bad}', encoding='utf-8')
            with self.assertRaises(ValueError): n.load_jsonl(p)

    def test_roundtrip_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); inp = write_input(base/'input')
            before = n.sha(inp/'text_rows.jsonl')
            report, _, _ = n.process_game(inp, base/'out')
            self.assertTrue(report['serialized_preservation_verified'])
            self.assertEqual(before, n.sha(inp/'text_rows.jsonl'))

    def test_summary_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); inp = write_input(base/'input')
            with self.assertRaises(ValueError):
                n.process_game(inp, base/'out', collector_summary={'text_rows':'2', 'pitch_rows':'0', 'status':'FETCHED'})

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); inp = write_input(base/'input'); out=base/'out'; out.mkdir()
            sentinel = out/'keep'; sentinel.write_text('unchanged')
            with self.assertRaises(ValueError): n.run(argparse.Namespace(input=inp,out=out,sample=True,expected_games=720))
            self.assertEqual(sentinel.read_text(), 'unchanged')

    def test_output_under_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inp=write_input(Path(d))
            with self.assertRaises(ValueError): n.run(argparse.Namespace(input=inp,out=inp/'out',sample=True,expected_games=720))

    def test_720_batch_control_and_missing_game(self):
        # Synthetic balanced schedule: each of 45 pairs meets 16 times = 720; each team 144.
        with tempfile.TemporaryDirectory() as d:
            base=Path(d); root=base/'season'; root.mkdir(); games=[]; summaries=[]
            teams=list(n.TEAMS)
            for i,a in enumerate(teams):
                for b in teams[i+1:]:
                    for repeat in range(16):
                        gid=f'g{len(games):04d}'
                        games.append({'gameId':gid,'awayTeamCode':a,'homeTeamCode':b})
                        summaries.append({'game_id':gid,'status':'FETCHED','text_rows':1,'pitch_rows':0})
                        write_input(root/'games',gid)
            n.save_json(root/'manifest.json', games)
            n.save_json(root/'inventory_check.json', {'inventory_passed':True,'selected_games':720,
                        'checked_days':199,'expected_days':199,'schedule_errors':[],'review_items':[],'stop_message':''})
            n.save_csv(root/'summary.csv',summaries,['game_id','status','text_rows','pitch_rows'])
            with contextlib.redirect_stdout(io.StringIO()):
                result=n.run(argparse.Namespace(input=root,out=base/'out',sample=False,expected_games=720))
            self.assertEqual(result,0)
            report=n.load_json(base/'out/run_report.json')
            self.assertEqual(report['normalized_games'],720)
            self.assertEqual(report['text_rows_preserved'],720)
            (root/'games/g0000/text_rows.jsonl').unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                result=n.run(argparse.Namespace(input=root,out=base/'out2',sample=False,expected_games=720))
            self.assertEqual(result,1)
            report=n.load_json(base/'out2/run_report.json')
            self.assertEqual(report['failed_games'],1)
            self.assertEqual(report['normalized_games'],719)
            self.assertEqual(report['status'],'INCOMPLETE')


if __name__ == '__main__': unittest.main()
