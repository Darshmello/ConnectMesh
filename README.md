# ConnectMesh — Federated AML Demo

Federated anti-money-laundering demo: one multinational bank's five regional
subsidiaries train a shared laundering-detection model with Flower, so no
transaction ever leaves its region. We compare **local-only vs. federated vs.
pooled** training on the IBM synthetic AML dataset (HI-Small).

See [`PLAN.md`](PLAN.md) for the full plan and [`AGENTS.md`](AGENTS.md) for
instructions if you're using an AI agent to help build this. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for how to branch, commit, and open PRs.

## Roles

| # | Role | Owns |
|---|------|------|
| 1 | Data lead | Partitions, time split, region assignment |
| 2 | Model + Flower lead | Baseline model, local/pooled/federated runs, `results.csv` |
| 3 | Evaluation lead | Metrics, gain table, new-region test, charts |
| 4 | Research + pitch lead | Problem doc, laws slide, competitor slide, Q&A prep |
| 5 | Demo lead | Streamlit page/slides, backup screenshots, demo script |

## Branching, in one line

One branch per role, named `role/<short-role-name>` (see `CONTRIBUTING.md`),
merged to `main` early and often so nobody works off a stale interface.

## Lunch infra checklist (do this before people scatter)

The plan already runs on strict interfaces (`data/region_<name>_train.parquet`,
`results.csv` with columns `region, setup, pr_auc, recall_at_fpr, n_train,
n_pos`). The single biggest risk after lunch is someone sitting idle because
an upstream file doesn't exist yet. Do these now, while everyone's in one
place to agree on details, so all 5 tracks can run in parallel unattended:

1. **Create the 5 role branches on `main`** (`git branch role/data` etc.) so
   everyone has a place to push the moment they're back — no "wait, what do I
   call my branch" friction.
2. **Commit the repo skeleton**: `data/`, `src/data/`, `src/model/`,
   `src/eval/`, `src/demo/`, `results/` — empty dirs with a `.gitkeep` if
   needed. Nobody should have to decide where their code lives.
3. **Commit a `requirements.txt`/`environment.yml`** pinned to versions that
   work with the Flower quickstart, so P2 isn't debugging installs solo.
4. **Person 1 commits placeholder partitions** — even dummy parquet files
   with the right columns and `is_laundering` label — so P2 and P3 can write
   code against the real schema without waiting on real data.
5. **Person 2 commits the fake `results.csv`** (per `PLAN.md`, this is
   already the plan for the 0:00–0:30 block) so P3 and P5 can build against
   it immediately.
6. **Person 5 commits a Streamlit/slide skeleton** that already reads
   `results.csv` and renders the table/chart placeholders — swapping fake
   numbers for real ones later is a one-line change, not new code.
7. **Agree and write down region → bank-ID assignment** (sizes and
   laundering rates should differ) — this is a judgment call that blocks P1
   and shouldn't be made solo after lunch.
8. **Open a PR template / branch protection on `main`** (see
   `CONTRIBUTING.md`) so merges after lunch don't need a live conversation to
   know what's expected.

If all 8 are done before lunch, every role can work heads-down and
independently afterward — nobody blocks on someone else's laptop.

## Evaluation demo: local decision and secure learning

The evaluation UI presents five fictional banks—Americas, EMEA, APAC, India,
and Small Sub—training a class-weighted logistic-regression model. It reports
PR-AUC as the headline metric and recall at a fixed false-positive rate; it
does not report accuracy.

### Data flow

1. Each bank process reads its own time-split
   `region_<name>_{train,test}.parquet` partitions and keeps local features
   and the `is_laundering` label in-process.
2. A Flower FedAvg server receives only model coefficient/intercept arrays and
   aggregate metrics such as `num-examples`.
3. The global model returns to each bank process for local PR-AUC and
   fixed-FPR-recall evaluation.

Raw transaction rows, account identifiers, and raw labels are not exchanged.
The partition fields are `timestamp`, `from_bank`, `to_bank`, `amount`,
`currency`, and `is_laundering`.

The demo compares local-only, federated, and pooled **synthetic-data**
benchmarks. Pooled training is an offline comparison, not part of the
federated production flow. Federated learning reduces raw-data-transfer
exposure but is not privacy by itself: model updates can leak information and
participants can poison training.
