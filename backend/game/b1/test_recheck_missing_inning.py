import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from recheck_missing_inning import GAME, compare, run

def fixture(texts):
    return {'code':200,'success':True,'result':{'textRelayData':{'gameId':GAME,'inn':9,
      'textRelays':[{'inn':1,'homeOrAway':'0','textOptions':[{'seqno':i+6,'text':t} for i,t in enumerate(texts)]}]}}}

class RecheckTests(unittest.TestCase):
    def test_same_still_missing(self):
        old=fixture(['2番ではない','2번타자 안치홍'])
        self.assertEqual(compare(old,old)['status'],'STILL_MISSING_IN_FRESH_RESPONSE')
    def test_candidate_not_auto_installed(self):
        r=compare(fixture(['2번타자 안치홍']),fixture(['1번타자 이주형','이주형 : 1루타','2번타자 안치홍']))
        self.assertEqual(r['status'],'RECOVERY_CANDIDATE_REVIEW_REQUIRED')
        self.assertFalse(r['restored_or_installed'])
    def test_runner_name_not_batter_result(self):
        old=fixture(['2번타자 안치홍']);r=compare(old,fixture(['1루주자 이주형 : 도루','2번타자 안치홍']))
        self.assertFalse(r['first_batter_result_text_found'])
    def test_title_without_result_not_recovery(self):
        r=compare(fixture(['2번타자 안치홍']),fixture(['1번타자 이주형','2번타자 안치홍']))
        self.assertEqual(r['status'],'RESPONSE_CHANGED_REVIEW_REQUIRED')
    def test_wrong_game_rejected(self):
        d=fixture(['2번타자 안치홍']);d['result']['textRelayData']['gameId']='wrong'
        with self.assertRaises(ValueError):compare(fixture(['x']),d)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):compare(fixture(['x']),fixture([]))
    def test_block_order_does_not_fake_added_rows(self):
        a=fixture(['A']);b=copy.deepcopy(a)
        a['result']['textRelayData']['textRelays'].append({'inn':1,'homeOrAway':'1','textOptions':[{'seqno':10,'text':'B'}]})
        b=copy.deepcopy(a);b['result']['textRelayData']['textRelays'].reverse()
        self.assertEqual(compare(a,b)['new_rows_not_in_old'],0)
    def test_one_request_preserves_original_and_saves_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'original'/'inning_01.json';p.parent.mkdir()
            raw=json.dumps(fixture(['2번타자 안치홍'])).encode();p.write_bytes(raw)
            calls=[]
            class Response:status_code=200;content=raw
            def get(url,**kwargs):calls.append(url);return Response()
            with contextlib.redirect_stdout(io.StringIO()):code=run(p,root/'out',get)
            self.assertEqual(code,0);self.assertEqual(len(calls),1);self.assertEqual(p.read_bytes(),raw)
            self.assertEqual(len(list((root/'out').glob('*.zip'))),1)
    def test_429_no_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'original'/'old.json';p.parent.mkdir();p.write_text(json.dumps(fixture(['x'])))
            calls=[]
            class Response:status_code=429
            def get(*args,**kwargs):calls.append(1);return Response()
            with contextlib.redirect_stdout(io.StringIO()):code=run(p,root/'out',get)
            self.assertEqual(code,1);self.assertEqual(len(calls),1)
            r=json.loads(next((root/'out').glob('*/recheck_report.json')).read_text(encoding='utf-8'))
            self.assertEqual(r['status'],'ACCESS_OR_RATE_LIMIT_STOP')

if __name__=='__main__':unittest.main()
