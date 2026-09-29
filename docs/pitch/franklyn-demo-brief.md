# ConnectMesh — Franklyn's five-bank demo brief

Owner: Franklyn Rosario, MBA-ITM — PM / Product

Scope confirmed by Franklyn on September 29, 2026: five banks; align with the backend team's federated model-training project. The separate three-bank case-review prototype is not part of this submission's demonstrated training pipeline.

## Product statement

ConnectMesh is a prototype for five banks to train an AML detection model collaboratively while keeping raw transaction records at the participating data holders during the federated run. We compare local-only, federated, and pooled training on synthetic data to measure whether collaboration improves detection.

For this experiment, the five participants are fictional bank-ID groupings in the IBM HI-Small synthetic dataset. They are not five verified real banks or actual geographic deployments. The planned deployment uses separate processes on one laptop. Do not describe those processes as secure isolation or five physical bank servers.

## The question the demo answers

Does a shared model improve held-out detection performance for participants relative to their local models, and how does it compare with a centralized pooled benchmark?

An improvement is a hypothesis until measured. Mixed or negative results are valid findings. Do not change the held-out test split after seeing scores to manufacture a win.

## Three-minute presentation script

**0:00–0:30 — Problem**

“Banks can observe different transaction patterns. A model trained on one participant's history may miss patterns represented elsewhere. Centralizing sensitive transaction records introduces governance, confidentiality, and competitive concerns. We ask whether banks can learn together while keeping raw records local during training.”

**0:30–1:00 — What we built**

“ConnectMesh compares three approaches using the same model family: each participant trains alone; five participants train collaboratively through Flower; and a pooled benchmark trains centrally. We use synthetic transactions and fictional participant groupings, with training and testing separated by time.”

**1:00–1:35 — Show execution**

“Here are the participating client processes and the Flower server. Each client trains against its assigned partition. The server aggregates model updates. These processes run on one laptop for this prototype.”

Only say this while showing an actual successful execution trace. If unavailable, replace with: “This is the intended architecture; an end-to-end federated run is not yet verified.”

**1:35–2:15 — Show measured results**

“We evaluate the three approaches on the same held-out records for each participant. Our headline metric is precision-recall AUC, which is more informative here than overall accuracy for rare positive examples. For [participant], local PR-AUC is [measured value] and federated PR-AUC is [measured value], a difference of [measured difference]. Across participants, the result is [improvement / mixed / no improvement].”

If results are not verified, say: “This screen contains layout placeholders. We are not claiming a performance improvement yet.” Do not read placeholder numbers as results.

**2:15–2:40 — Product value**

“The intended user is a bank's financial-crime analytics team. The product question is whether collaboration delivers useful detection performance without requiring routine centralization of raw transaction histories. A future pilot would measure both detection quality and investigator workload.”

**2:40–3:00 — Limits and close**

“This is a synthetic-data prototype, not proof of real-world effectiveness or regulatory compliance. Federated model updates can still leak information, and participants can introduce harmful updates. Our contribution today is a reproducible comparison and a clear account of what collaboration changes.”

## Franklyn's acceptance checklist

- [ ] Team agrees on one story: five participating banks, with fictional dataset groupings.
- [ ] The repository description and README no longer describe investigator staffing or conflict with the agreed framing.
- [ ] Data lead confirms dataset version, bank-ID grouping, features, and temporal split.
- [ ] Model lead supplies an actual Flower run log with five participants, rounds, and completion status.
- [ ] Evaluation lead confirms local/federated/pooled use the same held-out records and feature processing per participant.
- [ ] Any preprocessing fit uses training data only; duplicate/leakage checks are documented.
- [ ] Results CSV is traced to a run, command, code revision, and dataset/split identifiers.
- [ ] Per-participant PR-AUC and federated-minus-local differences are computed, not invented.
- [ ] Recall metric includes its false-positive-rate target and threshold-selection method. Do not imply equal operating points if measured differently.
- [ ] Placeholder warning is removed only after verified metrics replace the placeholders; replace it with the run identifier.
- [ ] Record a short backup video of the actual working demo.
- [ ] Confirm organizer submission deadline and required fields; the 4:40 PM target below is internal.

## Results handoff request — copy to teammates

“For the final demo, please provide the measured results CSV plus the exact run command, code revision, dataset/split ID, five client IDs, number of rounds, and completion log. Please identify any missing metrics or failed runs. We will label placeholders visibly and report mixed or negative findings honestly.”

## Internal schedule — Pacific time, September 29

| Target | Outcome |
|---|---|
| 1:45 PM | Scope and result interface locked; Franklyn rehearses opening |
| 2:30 PM | First complete training run and initial measured results, or explicit blocker |
| 3:30 PM | Feature freeze; use verified minimum scope |
| 4:00 PM | Results and demo checked against run evidence |
| 4:15 PM | Backup recording and pitch rehearsal |
| 4:40 PM | Internal submission target, subject to organizer deadline |
| 5:00 PM | Ready to present |

## Judge questions

**Are you training one model?** In the federated arm, yes: a shared model is trained from participant updates. Local and pooled models are comparison baselines.

**Does raw data ever get pooled?** The pooled benchmark intentionally centralizes synthetic data for comparison. The federated arm is designed to exchange model updates instead of raw transaction records. Show actual implementation/trace evidence before claiming that boundary was verified.

**Is this automatically private?** No. Keeping records local reduces one type of exposure; updates may leak information. Production protections and threat evaluation are outside this prototype.

**Is this cross-border legal compliance?** No. Geographic groupings are fictional, and the demo establishes no legal conclusion.

**Is Flower Chat the training system?** No. Our submission's training path uses Flower server/client components. The separately tested Flower Agent chat app is not evidence that federated training completed.

**Did collaboration help every bank?** Answer from verified per-participant results. Do not assume universal improvement.

## Current verification status

At inspection of main revision `362f7022281d750f74fcf51941b08e96585079f2`, results/README.md identifies results.csv as fake scaffolding. The Flower app README explicitly says its end-to-end result handling is not yet verified. These observations describe that revision, not teammates' unpushed work.

No verified training metric is supplied in this brief. The local dashboard warning is a presentation safeguard, not a backend fix. These branch changes have not been pushed or merged.
