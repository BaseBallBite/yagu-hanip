import unittest
from build_b1_plate_appearances import group_game

def make(spec):
    rows=[]
    for i,s in enumerate(spec):
        event,text,*extra=s
        rows.append({'play_id':str(i),'inning':1,'inning_half':extra[1] if len(extra)>1 else 'top',
          'event_type':event,'description':text,'pitch':{'pitch_number':extra[0]} if extra and extra[0] else None})
    return {'game_id':'g','plays':rows},{'ordered_play_ids':[r['play_id'] for r in rows]}
def group(spec):return group_game(*make(spec))

class PATests(unittest.TestCase):
    def test_normal_and_related_runner(self):
        r=group([('batter_announcement','1번타자 A'),('pitch','1구 타격',1),('single','A : 1루타'),
                 ('run_scored','3루주자 B : 홈인'),('batter_announcement','2번타자 C'),('walk','C : 볼넷')])
        self.assertEqual(len(r['groups']),2)
        self.assertEqual(r['groups'][0]['related_runner_play_ids'],['3'])
        self.assertEqual(r['groups'][0]['group_status'],'source_boundaries_observed')
    def test_repeat_announcement_not_new_pa(self):
        r=group([('batter_announcement','1번타자 A'),('pitch','1구 볼',1),
                 ('batter_announcement','1번타자 A'),('pitch','2구 타격',2),('single','A : 1루타')])
        self.assertEqual(len(r['groups']),1)
    def test_pinch_hitter_mid_pa(self):
        r=group([('batter_announcement','1번타자 A'),('pitch','1구 볼',1),
                 ('batter_announcement','대타 B'),('pitch','2구 타격',2),('single','B : 1루타')])
        self.assertEqual(len(r['groups']),1)
        self.assertEqual(r['groups'][0]['announced_batter_names'],['A','B'])
    def test_pinch_after_result_new_pa(self):
        r=group([('batter_announcement','1번타자 A'),('walk','A : 볼넷'),('batter_announcement','대타 B'),('single','B : 1루타')])
        self.assertEqual(len(r['groups']),2)
    def test_third_runner_out_not_completed_pa(self):
        r=group([('batter_announcement','1번타자 A'),('pitch','1구 볼',1),('caught_stealing','1루주자 B : 도루실패'),
                 ('inning_start','1회말',None,'bottom')])
        self.assertEqual(r['groups'][0]['completion_status'],'completion_unknown')
        self.assertFalse(r['groups'][0]['official_pa_count_eligible'])
    def test_correction_multiple_results_not_new_pa(self):
        r=group([('batter_announcement','1번타자 A'),('groundout','A : 땅볼 아웃'),
                 ('video_review','판독'),('single','A : 1루타')])
        self.assertEqual(len(r['groups']),1)
        self.assertIn('multiple_batter_result_rows',r['groups'][0]['review_flags'])
    def test_missing_announcement(self):
        r=group([('pitch','1구 볼',1),('walk','A : 볼넷')])
        self.assertEqual(r['groups'][0]['group_status'],'review_required')
    def test_reset_not_silently_split(self):
        r=group([('batter_announcement','1번타자 A'),('pitch','1구 볼',1),('pitch','1구 볼',1)])
        self.assertEqual(len(r['groups']),1)
        self.assertIn('pitch_number_reset_without_result',r['groups'][0]['review_flags'])
    def test_halves_never_merged(self):
        r=group([('batter_announcement','1번타자 A'),('walk','A : 볼넷'),('pitch','1구 볼',1,'bottom')])
        self.assertEqual(len(r['groups']),2)
    def test_stable_id_despite_following_rows(self):
        s=[('batter_announcement','1번타자 A'),('walk','A : 볼넷')]
        self.assertEqual(group(s)['groups'][0]['plate_appearance_id'],group(s+[('batter_announcement','2번타자 B')])['groups'][0]['plate_appearance_id'])

if __name__=='__main__':unittest.main()
