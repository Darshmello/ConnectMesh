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

## Roles (5 people)
| # | Role | Owns |
|---|------|------|
| 1 | Data lead | Load data, verify columns, time split, group banks into 5 regions (different sizes and laundering rates), save partitions |
| 2 | Model + Flower lead | Baseline model, class weighting, local / pooled runs, Flower simulation, saves `results.csv` |
| 3 | Evaluation lead | Metrics code, gain table, new-region test, privacy-noise run, charts |
| 4 | Research + pitch lead | Problem doc, laws slide, competitor slide (Swift, Consilient, Aurora, Banking Circle), judge Q&A, architecture diagram |
| 5 | Demo lead | Streamlit page or slides that display results, backup screenshots, demo script |

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
