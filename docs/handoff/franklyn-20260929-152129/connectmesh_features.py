import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[k]='1'
import sys,time,json,csv,socket,subprocess,warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,log_loss
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings('ignore',category=ConvergenceWarning)
ROOT=Path(__file__).resolve().parents[2]
REGIONS=['americas','emea','apac','india','small_sub']
ROUNDS=5




def features(f):
    formats=['Cash','Cheque','Credit Card','Bitcoin','ACH','Wire','Reinvestment']
    currencies=['Euro','Canadian Dollar','US Dollar','Bitcoin',
        'Australian Dollar','UK Pound','Ruble','Shekel','Swiss Franc',
        'Mexican Peso','Brazil Real','Yuan','Rupee','Saudi Riyal','Yen']
    def onehot(series, values):
        text=series.astype(str)
        return np.column_stack(
            [(text==v).to_numpy(dtype=float) for v in values]
            +[(~text.isin(values)).to_numpy(dtype=float)])
    amount=np.log1p(f.amount.to_numpy(dtype=float))/10.0
    stamp=pd.to_datetime(f.timestamp)
    hour=(stamp.dt.hour+stamp.dt.minute/60).to_numpy()
    kind=onehot(f['Payment Format'],formats)
    currency=onehot(f['Payment Currency'],currencies)
    numeric=np.column_stack([
        amount,np.sin(2*np.pi*hour/24),np.cos(2*np.pi*hour/24),
        (stamp.dt.dayofweek>=5).to_numpy(dtype=float),
        (f['Payment Currency']==f['Receiving Currency']).to_numpy(dtype=float)])
    return np.column_stack([numeric,kind,currency,kind*amount[:,None]])

def load(r):
    frames=[pd.read_parquet(ROOT/'data'/f'region_{r}_{s}.parquet')
            for s in ['train','test']]
    cutoff=pd.to_datetime(frames[1].timestamp).min()
    frames[0]=frames[0][pd.to_datetime(frames[0].timestamp)<cutoff].copy()
    for f in frames:
        assert len(f)>0 and f.is_laundering.isin([0,1]).all()
        assert np.isfinite(f.amount).all() and (f.amount>=0).all()
    assert frames[0].is_laundering.nunique()==2
    return [(features(f),f.is_laundering.to_numpy()) for f in frames]

def model():
    m=LogisticRegression(max_iter=20,warm_start=True,
        class_weight='balanced',random_state=42)
    m.classes_=np.array([0,1])
    m.coef_=np.zeros((1,37))
    m.intercept_=np.zeros(1)
    return m

def weights(m):
    return [m.coef_.copy(),m.intercept_.copy()]

def assign(m,p):
    m.coef_,m.intercept_=[np.array(v) for v in p]

def measure(m,tr,te):
    y=te[1]
    s=m.predict_proba(te[0])[:,1]
    threshold=np.quantile(
        m.predict_proba(tr[0][tr[1]==0])[:,1],.99,method='higher')
    return dict(
        pr_auc=float(average_precision_score(y,s)) if y.sum() else '',
        recall_at_fpr=float((s[y==1]>threshold).mean()) if y.sum() else '',
        n_train=len(tr[1]),n_pos=int(tr[1].sum()),
        test_fpr=float((s[y==0]>threshold).mean()) if (y==0).any() else None)

if len(sys.argv)>1:
    import flwr as fl
    role,address,out=sys.argv[1:4]
    out=Path(out)
    if role=='server':
        class Strategy(fl.server.strategy.FedAvg):
            def aggregate_fit(self,r,results,failures):
                assert len(results)==5 and not failures, 'Five clients required'
                p,metrics=super().aggregate_fit(r,results,failures)
                np.savez(out/'federated_model.npz',
                         *fl.common.parameters_to_ndarrays(p))
                return p,metrics
        strategy=Strategy(
            min_fit_clients=5,min_evaluate_clients=5,min_available_clients=5,
            fraction_fit=1.,fraction_evaluate=1.,accept_failures=False,
            initial_parameters=fl.common.ndarrays_to_parameters(weights(model())))
        fl.server.start_server(
            server_address=address,strategy=strategy,
            config=fl.server.ServerConfig(num_rounds=ROUNDS,round_timeout=120))
    else:
        tr,te=load(role)
        m=model()
        class Client(fl.client.NumPyClient):
            def get_parameters(self,config):
                return weights(m)
            def fit(self,p,config):
                assign(m,p)
                m.fit(*tr)
                return weights(m),len(tr[1]),{}
            def evaluate(self,p,config):
                assign(m,p)
                (out/f'{role}.json').write_text(json.dumps(measure(m,tr,te)))
                return float(log_loss(
                    te[1],m.predict_proba(te[0]),labels=[0,1])),len(te[1]),{}
        fl.client.start_client(
            server_address=address,client=Client().to_client(),insecure=True)
    sys.exit()

out=ROOT/'results'/('features-'+time.strftime('%Y%m%d-%H%M%S'))
out.mkdir(parents=True)
rows=[]
details={}

def add(r,setup,result):
    details[r+'/'+setup]=result
    rows.append(dict(region=r,setup=setup,
        **{k:result[k] for k in
           ['pr_auc','recall_at_fpr','n_train','n_pos']}))

data={r:load(r) for r in REGIONS}
print('Data checks passed. Training local and pooled models.',flush=True)
for r,(tr,te) in data.items():
    m=model()
    for _ in range(ROUNDS):
        m.fit(*tr)
    add(r,'local',measure(m,tr,te))
    np.savez(out/f'local_{r}.npz',*weights(m))

pooled=tuple(np.concatenate([data[r][0][i] for r in REGIONS]) for i in [0,1])
m=model()
for _ in range(ROUNDS):
    m.fit(*pooled)
for r,(_,te) in data.items():
    add(r,'pooled',measure(m,pooled,te))
np.savez(out/'pooled_model.npz',*weights(m))
del data,pooled

with socket.socket() as s:
    s.bind(('127.0.0.1',0))
    address='127.0.0.1:'+str(s.getsockname()[1])
processes=[]
logs=[]
try:
    for role in ['server']+REGIONS:
        log=(out/f'{role}.log').open('w')
        logs.append(log)
        processes.append(subprocess.Popen(
            [sys.executable,__file__,role,address,str(out)],
            stdout=log,stderr=subprocess.STDOUT))
        if role=='server':
            time.sleep(2)
    print('Five Flower clients started; logs:',out,flush=True)
    deadline=time.monotonic()+360
    while any(p.poll() is None for p in processes):
        if any(p.poll() not in [None,0] for p in processes):
            raise RuntimeError('Client/server failed; inspect logs in '+str(out))
        if time.monotonic()>deadline:
            raise TimeoutError('Six-minute deadline; inspect logs')
        time.sleep(.5)
    assert all(p.returncode==0 for p in processes)
finally:
    for p in processes:
        if p.poll() is None:
            p.terminate()
    for log in logs:
        log.close()

for r in REGIONS:
    add(r,'federated',json.loads((out/f'{r}.json').read_text()))
with (out/'results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
(out/'details.json').write_text(json.dumps(details,indent=2))
table=pd.DataFrame(rows).pivot(index='region',columns='setup',values='pr_auc')
(out/'index.html').write_text(
    '<html><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<style>body{font:18px system-ui;background:#eef5f6;color:#153348;margin:5%}'
    'table{background:white;border-collapse:collapse}td,th{padding:16px}'
    'a{color:teal}</style><h1>ConnectMesh</h1>'
    '<h2>Five clients. Five completed Flower rounds.</h2>'
    '<p>Measured average precision. Team-provided IBM-derived partitions; original provenance not independently verified. '
    'Fictional bank groupings; fixed test records.</p>'+table.to_html()+
    '<p>Feature experiment: 37 fixed inputs with twenty optimizer '
    'iterations per round; convergence is not guaranteed. Improvements are '
    'not assumed.</p><p>Recall thresholds use training negatives; actual test '
    'FPR is in details.json. Separate processes do not provide secure isolation.'
    '</p><p><a href="results.csv">Results CSV</a> | '
    '<a href="details.json">Evaluation details</a></p>')
print('COMPLETE: 15 measured results. Saved:',out,flush=True)
print(table.to_string())
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import webbrowser
print('Open http://127.0.0.1:8769 — keep this terminal open',flush=True)
webbrowser.open('http://127.0.0.1:8769')
ThreadingHTTPServer(
    ('127.0.0.1',8769),
    partial(SimpleHTTPRequestHandler,directory=str(out))
).serve_forever()
