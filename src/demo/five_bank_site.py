"""Local results viewer; does not start or verify Flower training."""
import csv, hashlib, io, json, math, argparse, webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[2]
RESULTS=ROOT/'results/results.csv'
PLACEHOLDER_SHA='c8ff2badb46c804fb47bf84878b9e90d580ce2605c45c5580ed914b81744c199'
REGIONS=('americas','emea','apac','india','small_sub')
def read_results(path=RESULTS):
    raw=path.read_bytes()
    if len(raw)>1000000: raise ValueError('Results file exceeds 1 MB')
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if set(reader.fieldnames or ())!={'region','setup','pr_auc','recall_at_fpr','n_train','n_pos'}: raise ValueError('CSV must use the agreed six-column interface')
    rows=[];seen=set()
    for row in reader:
        key=(row['region'],row['setup'])
        if key[0] not in REGIONS or key[1] not in ('local','federated','pooled') or key in seen: raise ValueError('Unexpected or duplicate participant/setup')
        seen.add(key);r={'region':key[0],'setup':key[1]}
        for f in ('pr_auc','recall_at_fpr'):
            v=float(row[f]) if row[f] and row[f].strip() else None
            if v is not None and (not math.isfinite(v) or not 0<=v<=1): raise ValueError(f+' must be blank or between 0 and 1')
            r[f]=v
        for f in ('n_train','n_pos'):
            v=int(row[f]) if row[f] and row[f].strip() else None
            if v is not None and v<0: raise ValueError('Negative count')
            r[f]=v
        if r['n_train'] is not None and r['n_pos'] is not None and r['n_pos']>r['n_train']: raise ValueError('Positive count exceeds training count')
        rows.append(r)
    sha=hashlib.sha256(raw).hexdigest()
    return {'status':'placeholder' if sha==PLACEHOLDER_SHA else 'unverified','sha256':sha,'rows':rows}
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path=='/': body=Path(__file__).with_name('five_bank_site.html').read_bytes();kind='text/html; charset=utf-8';status=200
        elif self.path=='/api/results':
            kind='application/json'
            try: body=json.dumps(read_results(),allow_nan=False).encode();status=200
            except (ValueError,OSError,TypeError,KeyError) as exc: body=json.dumps({'error':str(exc)}).encode();status=400
        else: body=b'Not found';kind='text/plain';status=404
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);url=f'http://127.0.0.1:{server.server_port}'
    print(f'ConnectMesh five-bank site: {url}\nDisplay only; training is not started.',flush=True)
    if not a.no_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
