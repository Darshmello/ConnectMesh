# results/

- `results.csv` — the real results. Columns `region, setup, pr_auc,
  recall_at_fpr, n_train, n_pos`; `setup` in `{local, federated, pooled}`;
  15 rows (5 regions x 3 setups). Validate any time:
  `.venv/bin/python src/model/flower_app/aml_fl/results_io.py`
- `federated_model.npz` — the final federated weights (776 bytes) behind the
  `federated` rows. Re-score with `.venv/bin/python src/model/evaluate_federated.py`.
- `runs/` — provenance: the logs of each Flower run (see below).

## How the numbers were produced
- `local` and `pooled`: `src/model/run_baselines.py` (Darsh's machine).
- `federated`: one 5-process Flower run (1 superlink + 5 supernodes, 20 rounds
  x 5 local iterations = the same 100-iteration budget as the baselines),
  run on a 16 GB Mac from branch `role/model` at commit `e630ac2`. The weights
  were then scored on Darsh's machine with `evaluate_federated.py`, the same
  scoring code as the baselines. Scores were also re-checked against the
  scores computed on the 16 GB machine: identical to 5 decimals.
- Data: IBM HI-Small (synthetic), `data/region_*_{train,test}.parquet`,
  80/20 time split. Regions are fictional groupings of bank IDs.

## Runs
- `runs/2026-09-29_federated_5bank/` — SUCCESS. 20/20 rounds, 5/5 nodes
  sampled every round, no UNAUTHENTICATED / "Task stopped" lines, 359 s.
  Paths inside the logs refer to the machine that ran it.
- `runs/2026-09-29_federated_5bank/per_round_pr_auc.csv` — the per-round
  monitoring number from the server log (mean test PR-AUC over the 5 banks,
  weighted by test size). Not the results.csv metric; noisy, peak 0.245 at
  round 18, 0.201 at round 20 (the model we report).

Earlier attempts on an 8 GB Mac failed (a client process stalled at startup,
Flower's 30 s task token expired, round 1 never completed; cause not proven).
Those logs are not kept here. All numbers in this folder come from the single
successful 16 GB run above.

## Caveats (read before quoting numbers)
- One run, one seed. Regions have only 51-84 training positives, so small
  differences are within noise.
- Result is mixed: federated beats local for india and emea, loses for apac
  and small_sub, and americas is unlearnable (about 0.001 in every setup).
