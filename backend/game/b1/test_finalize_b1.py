import contextlib,copy,io,tempfile,unittest
from pathlib import Path
import finalize_b1 as f

def fixture(gid='g1'):
    s={'game_id':gid,'source_ref':gid+'/t0','text':'A : 볼넷','seqno':1,'inning':1,'half_raw':'0','relay_no':1,'source_file':'inning_01.json','block_index':0,'raw':{'text':'A : 볼넷','seqno':1}}
    p={'play_id':f.sid(gid,'play',s['source_ref']),'source_record':s,'description':s['text'],'event_type':'walk','inning':1,'inning_half':'top','pitch':None,'review_flags':[]}
    return {'game_id':gid,'schema_version':'b1-row-v1.1','plays':[p],'tracking_records':[],'timeline_review_required':False,'dataset_revision':'test'}

class Tests(unittest.TestCase):
    def test_preservation(self):
        d=fixture();old=copy.deepcopy(d);r=f.select_game(d)
        self.assertEqual(d,old);self.assertEqual(r['text_rows_accounted_for'],1)
        self.assertFalse(r['semantic_review_complete']);self.assertFalse(r['state_reconstruction_complete'])
    def test_notice_not_event(self):
        d=fixture();d['plays'][0]['event_type']='video_review';r=f.select_game(d)
        self.assertEqual(r['event_candidate_ids'],[]);self.assertEqual(len(r['notice_ids']),1);self.assertEqual(len(r['pending_semantics']),1)
    def test_unknown_blocks(self):
        d=fixture();d['plays'][0]['event_type']='unknown';self.assertEqual(f.select_game(d)['status'],'BLOCKED')
    def test_unreviewed_flags_block(self):
        for game in (True,False):
            d=fixture()
            if game:d['timeline_review_required']=True
            else:d['plays'][0]['review_flags']=['seqno_collision_review']
            self.assertEqual(f.select_game(d)['status'],'BLOCKED')
    def test_admin_accounted(self):
        d=fixture();d['plays'][0]['event_type']='separator';r=f.select_game(d)
        self.assertFalse(r['ordered_play_ids']);self.assertEqual(len(r['excluded_from_sequence']),1)
    def test_reach_not_guessed(self):
        d=fixture();d['plays'][0]['event_type']='reach_unspecified';r=f.select_game(d)
        self.assertEqual(r['pending_semantics'][0]['event_type'],'reach_unspecified')
    def test_changed_plan_source_rejected(self):
        with self.assertRaises(ValueError):f.select_game(fixture(),{'game_id':'g1','source_text_sha256':'bad'})
    def test_invalid_identity_rejected(self):
        for mutation in ['id','duplicate','game','description']:
            d=fixture();p=d['plays'][0]
            if mutation=='id':p['play_id']='bad'
            if mutation=='duplicate':d['plays']*=2
            if mutation=='game':p['source_record']['game_id']='bad'
            if mutation=='description':p['description']='bad'
            with self.assertRaises(ValueError):f.select_game(d)
    def test_order_decrease_blocks(self):
        d=fixture();p=copy.deepcopy(d['plays'][0]);p['source_record']['source_ref']='g1/t1';p['play_id']=f.sid('g1','play','g1/t1');p['source_record']['seqno']=0;d['plays'].append(p)
        self.assertEqual(f.select_game(d)['status'],'BLOCKED')
    def test_repeated_pitch_blocks(self):
        d=fixture();a=d['plays'][0];a['event_type']='pitch';a['pitch']={'pitch_id':f.sid('g1','pitch','g1/t0'),'source_pitch_id':'p','tracking_status':'matched','tracking_id':f.sid('g1','tracking','g1/p0')}
        tr={'tracking_id':a['pitch']['tracking_id'],'source_record':copy.deepcopy(a['source_record'])};tr['source_record']['source_ref']='g1/p0';tr['source_record']['raw']={'pitchId':'p'};d['tracking_records']=[tr]
        b=copy.deepcopy(a);b['source_record']['source_ref']='g1/t1';b['play_id']=f.sid('g1','play','g1/t1');b['pitch']['pitch_id']=f.sid('g1','pitch','g1/t1');d['plays'].append(b)
        self.assertEqual(f.select_game(d)['status'],'BLOCKED')
    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            with self.assertRaises(ValueError):f.run(p/'input',p,{'games':[]})
    def test_720_and_tampered_input(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);root=p/'input';root.mkdir();reports=[];teams=['HT','SK','KT','LG','LT','SS','OB','NC','WO','HH']
            for i,a in enumerate(teams):
                for b in teams[i+1:]:
                    for rep in range(16):
                        gid='g'+str(len(reports));d=fixture(gid);d['metadata_raw']={'awayTeamCode':a,'homeTeamCode':b};path=root/'games'/gid/'normalized_game.json';f.write(path,d)
                        reports.append({'game_id':gid,'output_sha256':f.file_hash(path),'text_rows_output':1,'pitch_rows_output':0})
            f.write(root/'game_reports.json',reports);f.write(root/'run_report.json',{'scope':'full','status':'STRUCTURAL_PASS','schema_version':'b1-row-v1.1','selected_games':720,'processed_games':720,'normalized_games':720,'failed_games':0,'text_rows_preserved':720,'pitch_rows_preserved':0})
            with contextlib.redirect_stdout(io.StringIO()):code=f.run(root,p/'output',{'games':[]})
            self.assertEqual(code,0);self.assertEqual(f.read(p/'output/finish_report.json')['processed_games'],720)
            (root/'games/g0/normalized_game.json').write_text('{}')
            with contextlib.redirect_stdout(io.StringIO()):code=f.run(root,p/'badoutput',{'games':[]})
            self.assertEqual(code,1);self.assertEqual(f.read(p/'badoutput/finish_report.json')['status'],'INCOMPLETE')
if __name__=='__main__':unittest.main()
