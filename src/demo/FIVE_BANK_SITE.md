# Five-bank presentation site

Run from the repository root with Python 3.10+ (no extra packages):

```bash
python3 src/demo/five_bank_site.py
```

Open http://127.0.0.1:8766. Keep Terminal open. The port differs from the earlier three-bank backup (8765). This site does not alter or start the training system or the separate Flower Chat app.

## Connect backend output

Replace `results/results.csv` with the team's output using the existing six-column contract. Press Refresh results. The original placeholder file is identified by exact SHA-256. Any different file is UNVERIFIED, not automatically validated experiment evidence. Verify the run log, split, preprocessing, evaluation and metric definitions separately before showing measured performance claims. Metrics are hidden by default, including on refresh. A checkbox reveals labeled values for inspection. Missing values remain missing. No made-up performance values or runtime status are added.

Five group IDs are `americas`, `emea`, `apac`, `india`, `small_sub`; setups are `local`, `federated`, `pooled`. These names are fictional groupings, not actual locations. This is a results display, not a live Flower dashboard. It sends no data to external services and binds only to localhost.

## Verify

```bash
python3 src/demo/test_five_bank_site.py
```

Four automated tests passed, including HTTP responses, placeholder recognition, missing values, and invalid/duplicate result rejection. JavaScript syntax checked. Browser visual and click testing has not been completed in the build environment; check on the Mac before presenting.

Training dependencies stay separate: repository requirements.txt pins flwr 1.30.0. The earlier Flower Agent chat used 1.38.0. This viewer uses only Python standard library and does not change either environment.
