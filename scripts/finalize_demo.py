"""Build an offline dashboard from a hash-matched ConnectMesh handoff. No training."""
import argparse
import csv
import hashlib
import html
import json
import math
import shutil
from pathlib import Path

REGIONS = ('americas', 'emea', 'apac', 'india', 'small_sub')
SETUPS = ('local', 'federated', 'pooled')

def build(repo):
    candidates = sorted((repo / 'docs/handoff').glob('franklyn-*/manifest.json'))
    if not candidates:
        raise ValueError('No saved handoff found in this repository.')
    source = candidates[-1].parent
    raw = (source / 'results.csv').read_bytes()
    manifest = json.loads((source / 'manifest.json').read_text())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != manifest.get('results_sha256'):
        raise ValueError('CSV hash differs from saved manifest. Stopping.')
    records = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    expected = {(r, s) for r in REGIONS for s in SETUPS}
    if len(records) != 15 or {(r['region'], r['setup']) for r in records} != expected:
        raise ValueError('Expected exactly five groups and three setups.')
    values = {(r['region'], r['setup']): float(r['pr_auc']) for r in records}
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in values.values()):
        raise ValueError('Average precision must be finite and between zero and one.')
    local_wins = sum(values[r, 'local'] > values[r, 'federated'] for r in REGIONS)
    finding = f'Local models scored higher than the federated model in {local_wins} of 5 groups.'
    panels, rows = [], []
    scale = max(values.values()) or 1
    for region in REGIONS:
        label = region.replace('_', ' ').title()
        bars = ''.join(
            f'<div class="bar"><span>{setup.title()}</span><div class="track">'
            f'<div class="fill {setup}" style="width:{100*values[region,setup]/scale:.4f}%"></div>'
            f'</div><b>{values[region,setup]:.6f}</b></div>' for setup in SETUPS)
        panels.append(f'<article><h3>{label}</h3>{bars}</article>')
        scores = ''.join(f'<td>{values[region,s]:.6f}</td>' for s in SETUPS)
        delta = values[region,'federated'] - values[region,'local']
        rows.append(f'<tr><th>{label}</th>{scores}<td>{delta:+.6f}</td></tr>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ConnectMesh | Measured Flower experiment</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f6f8;color:#153348;font:16px/1.6 system-ui}
main{max-width:1120px;margin:auto;padding:32px 24px}nav{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:1px solid #ccdce3;padding-bottom:18px}
.eyebrow{color:#087d82;font-size:12px;letter-spacing:.12em;text-transform:uppercase;font-weight:700}
h1{font-size:clamp(42px,7vw,76px);letter-spacing:-3px;line-height:1.1;margin:24px 0 12px}h2{font-size:26px}h3{margin:0 0 14px}.lead{font-size:23px;max-width:820px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px}
article,.panel{padding:24px;background:white;border:1px solid #d8e4e9;border-radius:15px;margin-bottom:16px}
.finding{background:#fff3da;border-left:5px solid #b58129;padding:20px 24px;border-radius:10px;margin:26px 0}
.bar{display:grid;grid-template-columns:78px 1fr 82px;gap:10px;align-items:center;font-size:13px;margin:12px 0}.track{height:14px;background:#edf2f5;border-radius:4px;overflow:hidden}.fill{height:100%}.local{background:#416ca5}.federated{background:#087d82}.pooled{background:#899ba7}
.scroll{overflow:auto}table{width:100%;border-collapse:collapse;min-width:630px}th,td{text-align:right;padding:12px;border-bottom:1px solid #dce5e9;font-variant-numeric:tabular-nums}th:first-child{text-align:left}small,.muted{color:#526a79}a{color:#087d82;font-weight:650}code{overflow-wrap:anywhere;font-size:12px}footer{border-top:1px solid #ccdce3;padding:24px 0}summary{cursor:pointer;font-weight:700}
@media(max-width:700px){.grid,.charts{grid-template-columns:1fr}main{padding:20px 14px}.bar{grid-template-columns:70px 1fr 75px}}@media print{article{break-inside:avoid}}
</style><main><nav><b>AIZOYA · ConnectMesh</b><span>Stanford hackathon · Franklyn + Adam</span></nav>
<header><p class="eyebrow">Five-bank synthetic AML research</p><h1>Measure what<br>collaboration adds.</h1><p class="lead">Compare five local models, one shared Flower model, and a pooled reference using the same test records for each group.</p></header>
<div class="finding"><strong>FINDING</strong><br>FINDING_TEXT<p>This run does not demonstrate a federated advantage. It provides a reproducible comparison and a starting point for investigating differences between participants.</p></div>
<div class="grid"><article><h3>Local</h3>Each group trains on its own partition.</article><article><h3>Federated</h3>Five client processes exchange model updates with a Flower server.</article><article><h3>Pooled</h3>A reference model trains on combined synthetic records.</article></div>
<h2>Measured average precision</h2><p class="muted">Higher is better. This is average precision, not accuracy. All bars share a scale from 0 to SCALE.</p><div class="charts">CHARTS</div>
<section class="panel scroll"><table><thead><tr><th>Group</th><th>Local</th><th>Federated</th><th>Pooled</th><th>Fed − local</th></tr></thead><tbody>ROWS</tbody></table></section>
<section class="panel"><h2>Evidence you can inspect</h2><p><a href="results.csv">Results CSV</a> · <a href="details.json">Evaluation details</a> · <a href="manifest.json">Run manifest</a> · <a href="server.log">Server log</a></p><p>Saved run: <code>SOURCE</code><br>CSV SHA-256: <code>DIGEST</code></p><p class="muted">The CSV matches its saved manifest. This integrity check does not independently validate the training or data provenance.</p>
<details><summary>Method and limits</summary><p>Five clients, five rounds, 37 fixed features, class-weighted logistic regression. Temporal train/test partitions; optimization convergence is not guaranteed. Feature exploration followed earlier test inspection, so this is exploratory evidence.</p><p>Team-provided IBM-derived synthetic partitions; original provenance not independently verified. Group names are fictional bank-ID buckets, not verified geographic locations.</p><p>Recall thresholds use training negatives. Actual test false-positive rates are recorded in evaluation details and may differ from 1%.</p><p>Separate processes on one laptop are not secure isolation. Model updates can leak information. These findings do not establish production AML performance or regulatory compliance.</p></details></section>
<footer>Saved experiment viewer. Opening this page does not run training.<br>Nebius integration has not been verified for this experiment.</footer></main>'''
    for key, value in {'FINDING_TEXT': finding, 'SCALE': f'{scale:.6f}', 'CHARTS': ''.join(panels), 'ROWS': ''.join(rows), 'SOURCE': html.escape(source.name), 'DIGEST': digest}.items():
        page = page.replace(key, value)
    target = repo / 'docs/final-demo'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('results.csv', 'details.json', 'manifest.json', 'server.log'):
        shutil.copy2(source / name, target / name)
    (target / 'index.html').write_text(page)
    (target / 'PITCH.md').write_text(
        '# ConnectMesh — 90-second demo\n\n'
        'Banks may hold different examples of suspicious activity. Our question is whether sharing model updates improves learning across five synthetic participant groups.\n\n'
        'We ran local, federated, and pooled training. Flower coordinates five client processes on one laptop. The dashboard compares average precision on the same test records for each participant.\n\n'
        + finding + ' We report that result rather than assuming collaboration helps. More data in a shared model did not automatically produce a better ranking in this experiment.\n\n'
        'The deliverable is a working experimental pipeline, saved model weights, execution logs, and measured results. Next we would investigate distribution differences and optimization using validation data, then evaluate on a fresh holdout.\n\n'
        'The data is synthetic, the groups are fictional, and process separation does not provide a privacy guarantee. Nebius use is not yet verified.\n')
    print('READY:', target / 'index.html')
    print(finding)
    return target

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path.home() / 'ConnectMesh-Franklyn')
    args = parser.parse_args()
    build(args.repo.resolve())
