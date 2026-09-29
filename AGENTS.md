# AGENTS.md

Instructions for AI agents working in this repository. Read this first, then `PLAN.md`.

## Project
Federated AML demo: one multinational bank with five regional subsidiaries trains a shared laundering-detection model with Flower, so no transaction leaves its region. We compare local-only vs. federated vs. pooled training on the IBM synthetic AML dataset (HI-Small), with regions assigned by bank ID.

This is a hackathon project with a few hours available. Prefer the simplest thing that produces the results chart.

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

### How to behave while roles are undecided
- Do not assume who owns a task or who will read your output. Address whoever is prompting you.
- If a task touches another role's area (for example, changing the data partitions while working on the model), say so and keep the change small.
- Do not rename files, columns or folders that others depend on (see Interfaces).
- If asked to decide who does what, offer a suggestion and let the team confirm.

## Fixed decisions
- **Data:** IBM synthetic AML dataset, HI-Small. Regions are fictional labels grouped by bank ID.
- **Model:** logistic regression with class weighting. The same model is used for local, federated and pooled runs.
- **Framework:** Flower simulation engine. Start from the official quickstart, because the API changes between versions.
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
