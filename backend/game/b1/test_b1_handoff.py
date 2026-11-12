import copy
import unittest
from build_b1_handoff import policy, build_game, EVENTS, CONTEXT, NOTICES

class ContractTests(unittest.TestCase):
    def test_all_types_have_safe_policy(self):
        for event in EVENTS | CONTEXT | NOTICES:
            with self.subTest(event=event):
                p = policy(event, [])
                self.assertFalse(p['can_use_as_verified_fact'])
                self.assertFalse(p['can_accumulate_outs_or_runs'])
    def test_reach_not_promoted_to_error_or_hit(self):
        self.assertEqual(policy('reach_unspecified', [])['disposition'], 'unresolved_reach_reason')
    def test_review_and_correction_not_results(self):
        for event in ['video_review', 'correction_notice', 'play_notice']:
            self.assertEqual(policy(event, [])['disposition'], 'context_review_required')
    def test_unknown_is_rejected(self):
        for event in ['unknown', 'invented', None]:
            with self.assertRaises(ValueError): policy(event, [])
    def test_flags_cannot_be_silently_cleared(self):
        self.assertEqual(policy('single', ['unexpected'])['disposition'], 'flagged_source_record')
    def test_source_untouched_and_no_state_invention(self):
        row={'play_id':'x','inning':1,'inning_half':'top','event_type':'reach_unspecified',
             'description':'선수 : 출루','source_record':{'source_ref':'source/x'},'pitch':None}
        data={'game_id':'g','plays':[row]}
        s={'ordered_play_ids':['x'],'pending_semantics':[{'play_id':'x','flags':['review']}],
           'field_limitations':[],'global_limitations':[],'excluded_from_sequence':[]}
        before=copy.deepcopy(data)
        result=build_game(data,s)['records'][0]
        self.assertEqual(data,before)
        self.assertEqual(result['description'],row['description'])
        for key in ['state_before','state_after','actor_player_id','plate_appearance_id']:
            self.assertIsNone(result[key])
        self.assertEqual(result['review_flags'],['review'])
        self.assertEqual(result['event_type'],'reach_unspecified')
    def test_duplicate_selection_rejected(self):
        row={'play_id':'x','inning':1,'inning_half':'top','event_type':'pitch',
             'description':'1구 볼','source_record':{'source_ref':'x'}}
        with self.assertRaises(ValueError):
            build_game({'game_id':'g','plays':[row]}, {'ordered_play_ids':['x','x'],
                'pending_semantics':[], 'field_limitations':[], 'global_limitations':[],
                'excluded_from_sequence':[]})

if __name__=='__main__': unittest.main()
