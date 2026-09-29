# Contributing

This applies equally to human teammates and AI agents working in this repo.
If you're an agent, read [`AGENTS.md`](AGENTS.md) first for project-specific
rules, then follow the workflow below.

## Branch naming

One branch per role, branched from `main`:

```
role/data           # partitions, time split, region assignment
role/model           # baseline model, local/pooled/federated runs
role/eval            # metrics, gain table, new-region test, charts
role/pitch           # problem doc, laws/competitor slides, Q&A
role/demo            # Streamlit page or slides, demo script
```

If you're doing a small fix outside your main role, use
`fix/<short-description>` instead of piggybacking it onto a role branch.

## Workflow

1. Branch from `main`: `git checkout -b role/<yours> main`.
2. Commit early and often. Small commits are easier for teammates to review
   under time pressure.
3. Push and open a PR into `main` as soon as you have something runnable —
   don't wait until it's "done." The plan depends on people building against
   real files (`results.csv`, partitions) as early as possible, per
   `PLAN.md`.
4. Merge your own PR once it's runnable and doesn't break the interfaces
   below. With 5 people and a few hours, don't block on review unless you
   touched someone else's files.
5. If you must touch a file outside your role (e.g. changing a partition
   schema while working on the model), say so in the PR description and in
   the team channel — don't rename or restructure without a heads-up.

## Interfaces — do not change without agreement

These are load-bearing; changing them silently breaks someone else's branch.

- Partitions: `data/region_<name>_train.parquet` and
  `data/region_<name>_test.parquet`, same columns, label column
  `is_laundering`.
- Results: `results.csv` with columns
  `region, setup, pr_auc, recall_at_fpr, n_train, n_pos`.
  `setup` is one of `local`, `federated`, `pooled`.

## Rules

- Never invent results. If a number isn't computed yet, write
  `[fill after experiment]`.
- Don't commit dataset files or credentials.
- Don't claim novelty or legal conclusions beyond what's cited — see the
  Honesty rules in `AGENTS.md`.
- Keep PRs small and runnable; say how to run what you wrote in the PR
  description.
