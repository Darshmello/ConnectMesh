# AGENTS.md

Instructions for AI agents working in this repository. Read this first, then `PLAN.md`.

## Project
Federated AML demo: **five separate banks** (a consortium, not subsidiaries of one company) train a shared laundering-detection model with Flower, so no bank's raw transaction data ever leaves its own machine. We compare local-only vs. federated vs. pooled training on the IBM synthetic AML dataset (HI-Small), with banks grouped into 5 "region" buckets by bank ID.

Why consortium, not subsidiaries: the dataset itself is built by IBM to model *multiple distinct banks* transacting with each other (confirmed against IBM's NeurIPS paper), not one company's internal ledger — there's no region/geography field, bank IDs are just anonymous integers. Subsidiaries also don't need an incentive to share data (HQ mandates it); separate banks do, and that incentive story is the actual pitch — see "Why Flower" below.

This is a hackathon project with a few hours available. Prefer the simplest thing that produces the results chart.

## Why Flower (first principles — use this framing in the pitch, not a multi-agent-framework comparison)

Good models need data. The most valuable data (patient records, bank transactions, phone keystrokes) can't be pooled onto one server, because of law, privacy, or competition — a bank sharing its raw transactions with a rival bank is both probably illegal and definitely unwise. So today, each bank's fraud model only ever sees that bank's own fraud patterns, and everyone else's history goes unused.

Flower lets multiple banks train one shared model together — each bank's raw data stays on its own machine; only model updates are exchanged — so the model learns from every bank's fraud history without any bank's data ever leaving its own server.

**What Flower actually is:** `flwr` (the package in `requirements.txt`) is, per its own GitHub README, "a framework for building federated AI systems" — a federated learning framework. It is **not** a multi-agent orchestration framework and should never be compared to LangGraph, CrewAI, or AutoGen — that's a category error. Flower's marketing homepage (flower.ai) has newer branding around "Collaborative Superintelligence" and a "Flower Agent" product — that is a separate, sparsely-documented commercial product, unrelated to the open-source `flwr` package this project installs and uses. Do not reference or build pitch claims on that branding; stick to what `flwr` (the package) documents itself as.

## Team
Five people work on this project, and their work is shared. **Who owns which task has not been decided yet.**

| Person | Contact | Role |
|---|---|---|
| Darsh | (fill in) | TBD. Interested in the model and Flower simulation |
| Teammate 2 | (fill in) | TBD |
| Teammate 3 | (fill in) | TBD |
| Teammate 4 | (fill in) | TBD |
| Teammate 5 | (fill in) | TBD |

Roles to be assigned (see `PLAN.md`): Data, Model + Flower, Evaluation, Research + pitch, Demo.

Update this table once the split is agreed. Do not put personal emails in this file if the repo is public.

### Quickstart for a teammate on their own laptop
1. `git clone https://github.com/Darshmello/ConnectMesh.git && cd ConnectMesh`
2. `git checkout role/<yours>` — data, model, eval, pitch, or demo.
3. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
4. Read this whole file, then `PLAN.md`, then look at the `src/<your-role>/`
   directory — there's already a runnable placeholder in it.
5. Work independently and push to your own branch. You do **not** need
   anyone else's laptop, and nobody needs yours — every branch already has
   the fake `data/region_*.parquet` and `results/results.csv`, so you can
   run and test your piece right now, before real data or real model runs
   exist. The one exception is the final integration run (real Flower
   server + 5 client processes together) — that happens once, near the
   end, on whichever single laptop the team picks then, not during
   individual work.

### How to behave while roles are undecided
- Do not assume who owns a task or who will read your output. Address whoever is prompting you.
- If a task touches another role's area (for example, changing the data partitions while working on the model), say so and keep the change small.
- Do not rename files, columns or folders that others depend on (see Interfaces).
- If asked to decide who does what, offer a suggestion and let the team confirm.

## Fixed decisions
- **Data:** IBM synthetic AML dataset, HI-Small. Regions ("banks" in the consortium framing) are fictional groupings assigned by bank ID.
- **Region assignment:** a hand-picked `bank_id → region` lookup table, checked into the repo (not computed inline), deliberately skewed in size and laundering rate — this is what makes the "federated beats local" and "gain from joining" results visible. See `PLAN.md`'s risk section: skew the split before ever tuning the model.
- **Model:** logistic regression with class weighting. The same model is used for local, federated and pooled runs.
- **Framework:** Flower, run as **real separate processes** (one Flower server + 5 client processes, all on one laptop, different terminals/ports) — not Flower's single-process simulation mode. This is deliberate: the pitch's core claim is that no region's data leaves its own process, and simulation mode would hold all 5 regions' data in one process's memory, which undercuts that claim. Start from the official server/client quickstart, because the API changes between versions.
- **Where it runs:** one laptop, 5 terminals/ports. Not multiple physical machines — avoids live-demo network risk for no loss of the actual claim (separate OS processes, no shared memory, still true and demoable).
- **Split:** train/test by time, never random.
- **Metrics:** PR-AUC (headline), recall at a fixed false-alarm rate, per-region gain over local. Never report accuracy (laundering is about 0.1% of transactions).

## Interfaces
- Partitions: `data/region_<name>_train.parquet` and `data/region_<name>_test.parquet`, same columns, label column `is_laundering`.
- Results: `results.csv` with columns `region, setup, pr_auc, recall_at_fpr, n_train, n_pos`. `setup` is one of `local`, `federated`, `pooled`.

## Non-goals
- Graph learning, cross-bank chain detection, LLMs or foundation models
- Production deployment
- Real legal or regulatory conclusions

## Honesty rules
- Never invent results. If a number is not computed, mark it `[fill after experiment]`.
- State that the data is synthetic and the regions are fictional wherever results are shown.
- Do not claim novelty. Swift, Consilient, BIS Project Aurora and Banking Circle already work on this.
- Do not claim federated learning is private by itself. Model updates can leak information and a dishonest participant can poison the model.
- Legal points are summaries of public sources, not legal advice.
- Do not commit dataset files or credentials.

## Working style
- Keep changes small and runnable. Say how to run what you wrote.
- Prefer one complete, copy-pasteable file over fragments.
- If something fails, report the real error instead of guessing.
