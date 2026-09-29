import importlib.util,json,tempfile,threading,unittest,urllib.request
from pathlib import Path
spec=importlib.util.spec_from_file_location('viewer',Path(__file__).with_name('five_bank_site.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
HEADER='region,setup,pr_auc,recall_at_fpr,n_train,n_pos\n'
class Tests(unittest.TestCase):
 def parse(self,text):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.csv';p.write_text(text);return v.read_results(p)
 def test_placeholder(self):
  r=v.read_results();self.assertEqual(r['status'],'placeholder');self.assertEqual(len(r['rows']),15)
 def test_blank_is_missing(self):
  r=self.parse(HEADER+'americas,local,,,10,1\n');self.assertIsNone(r['rows'][0]['pr_auc']);self.assertEqual(r['status'],'unverified')
 def test_bad_metrics_and_duplicate(self):
  for row in ['americas,local,NaN,,10,1\n','americas,local,1.1,,10,1\n','unknown,local,.2,,10,1\n','americas,local,.2,,10,11\n','americas,local,.2,,10,1\n'*2]:
   with self.subTest(row=row),self.assertRaises(ValueError):self.parse(HEADER+row)
 def test_http(self):
  server=v.ThreadingHTTPServer(('127.0.0.1',0),v.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   url='http://127.0.0.1:'+str(server.server_port)
   with urllib.request.urlopen(url) as r:self.assertIn(b'Five participating data groups',r.read())
   with urllib.request.urlopen(url+'/api/results') as r:self.assertEqual(json.load(r)['status'],'placeholder')
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
