# Project Plan: Federated AML Across One Bank's Regions

## One-line goal
Show that one multinational bank's regional models detect laundering better when trained together with Flower than alone, without any transaction leaving its region.

## The demo (definition of done)
1. One table + one chart: per region, PR-AUC for **local-only / federated / pooled**.
2. "Gain from joining" per region (federated minus local), smallest region highlighted.
3. New-region test: train on all regions but one, test on the held-out one.
4. Optional: one run with privacy noise on, showing the accuracy cost.
5. A 3-minute pitch: problem, laws (EU / India / China), prior work, results, honest limits.

## Non-goals (do not build)
- Graph learning or cross-bank chain detection
- LLMs or foundation models
- Real legal or regulatory claims beyond the public sources we cite
- A production system

## Fixed decisions
- Data: IBM synthetic AML dataset (HI-Small). Regions are fictional labels assigned by bank ID.
- Model: logistic regression with class weighting. Same model for local, federated and pooled.
- Framework: Flower simulation engine (start from the official quickstart).
- Split train/test **by time**, not randomly.
- Metrics: PR-AUC (headline), recall at fixed false-alarm rate, per-region gain over local. Never accuracy.

## Roles (assigned)

Branch names below are from `CONTRIBUTING.md` — branch from `main`, push early and
often, don't touch another role's interface files without saying so.

| # | Role | Person | Branch | Concrete SWE tasks |
|---|------|--------|--------|---------------------|
| 1 | Data lead | **Musa** | `role/data` | Download `HI-Small_Trans.csv` (see `src/data/make_real_partitions.py` docstring for the link — needs a Kaggle account); fill in the real `REGION_MAP` (bank IDs → 5 regions) in that file, deliberately skewed in size/rate per the risk section below; run it and confirm `data/region_*.parquet` looks right (row counts, laundering rate per region, no NaNs); pick which region gets held out for the new-region test. |
| 2 | Model + backend lead | **Darsh** | `role/model` | Own `src/model/flower_app/` end to end. Add real features to `FEATURES` in `aml_fl/task.py` (currently just `amount` — add payment format, currency, sender/receiver transaction frequency); write the local-only and pooled baseline scripts (plain sklearn, no Flower — these don't exist yet, only the federated path does); fix the two TODOs in `server_app.py` (`n_train`/`n_pos` not threaded through, `recall_at_fpr` not wired up); run the real 5-process Flower deployment (`src/model/flower_app/README.md` has the exact commands) and replace the fake `results.csv` with real output. |
| 2b | Flower + frontend | **Adam Franklyn** | `role/model` (Flower ops) + `role/demo` (frontend) | Flower side: write a script/Makefile that launches the server + 5 client processes in one command instead of 7 manual terminals (biggest live-demo risk right now is someone fat-fingering a port). Frontend side: extend `src/demo/app.py` — region selector, the "why federated" narrative text pulled from `docs/pitch/problem.md`, and make sure it survives `results.csv` going from fake to real numbers with zero code changes. |
| 3 | Evaluation | **Sahan** (backend) | `role/eval` | This role has no separate owner yet, so it's the natural fit for a second backend person: implement `recall_at_fpr()` in `src/eval/metrics.py` (currently `raise NotImplementedError`); build the new-region generalization test (train on 4 regions, evaluate on Musa's held-out one); wire `gain_table()`'s output into whatever chart P5/Adam's demo page renders. **Flag this explicitly to Sahan — I'm inferring this from "backend" being unclaimed elsewhere, not from anything they said themselves.** |
| 4 | Research + pitch | **unassigned** | `role/pitch` | Nobody is on this yet. `docs/pitch/problem.md`, `laws.md`, `competitors.md` are all fill-in-the-blank skeletons with nobody filling them, and there's no Q&A prep or architecture diagram owner. This is a real gap, not a small one — it's the entire narrative half of the pitch. Needs a 5th person or someone above giving up bandwidth once their build tasks are done. |

## Interfaces (agree in the first 15 minutes)
- Partitions: `data/region_<name>_train.parquet` and `..._test.parquet`, same columns, label column `is_laundering`.
- Results: `results.csv` with columns `region, setup, pr_auc, recall_at_fpr, n_train, n_pos`. `setup` is one of `local, federated, pooled`.
- Person 2 writes a **fake `results.csv` in the first 30 minutes** so persons 3 and 5 can build against it.

## Timeline (scale to the time you have; total about 4 hours)
| Block | Work |
|------|------|
| 0:00 - 0:30 | Agree on interfaces, download data, fake results file, roles confirmed |
| 0:30 - 1:30 | P1 partitions ready. P2 local and pooled baselines. P4 problem doc. P3 metrics code. P5 page skeleton |
| 1:30 - 2:30 | P2 Flower simulation running. P3 gain table and charts. P4 laws and competitor slides |
| 2:30 - 3:15 | Real results replace the fake file. New-region test and optional privacy run. P5 wires the charts in |
| 3:15 - 4:00 | Pitch rehearsal, backup screenshots, fix anything broken. No new features |

## Risks and fallbacks
- **Federated does not beat local:** make regions more different (rates, sizes), shrink the smallest. Do not tune the model first.
- **Flower API problems:** copy the official quickstart, change only the data loader and model.
- **Low absolute scores:** expected. Judge on the gaps between setups.
- **Time runs out:** ship local vs federated vs pooled only. Drop the new-region and privacy runs.

## Honest limits (say these out loud)
- Not novel: Swift, Consilient, BIS Aurora and Banking Circle already work on this.
- Synthetic data, fictional regions. This is a demonstration, not evidence of real-world performance.
- Federated learning reduces data-transfer exposure but is not privacy by itself. Model updates can leak information and a dishonest participant can poison the model.
