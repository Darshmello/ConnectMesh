# ConnectMesh — Collaborative Evidence Review

ConnectMesh is a hackathon prototype for reviewing anti-money-laundering model evidence before a human decides what to do next. The event-facing Flower AgentApp requests a numerical review and a methodological challenge from two peer workers on SuperGrid. A five-group federated-learning experiment supplies the evidence being reviewed.

## Demonstrated status — September 29, 2026, 5:22 PM Pacific

| Component | Observed result |
|---|---|
| Training evidence | Team-reported five-client, 20-round Flower run completed on a 16 GB RAM Mac; results and runbook are in `results/`. |
| Nebius inference | Direct Kimi inference succeeded. Two live review requests completed: numerical comparison and methodological challenge. |
| SuperGrid coordinator | AgentApp v0.3.2 run `791632745106363984` finished with status `completed`, but reported **Missing replies: 2. Review incomplete.** |
| Worker credentials | Earlier v0.2.0 worker logs showed Nebius HTTP 401. A corrected key passed a direct test, and the two-worker launcher was restarted. Successful peer replies after restart remain unverified. |
| End-to-end collaboration | **Not yet verified.** Coordinator completion and online nodes are insufficient proof of peer review. |
| Flower Hub publication | Not yet verified. |

The successful fallback sent two separate prompts to the **same Kimi model** through Nebius Token Factory. Those requests did **not** use SuperGrid messaging and do not constitute independent-model validation. Human review is required.

## How the proposed workflow works

1. Supply the measured experiment CSV and its limitations.
2. Ask one worker to calculate regional gains and losses.
3. Ask a second worker to challenge the interpretation and recommend a validation experiment.
4. Collect actual replies, identify missing or failed responses, and reconcile conclusions against the CSV.
5. Present the evidence to a human. No automated investigation decision, regulatory filing, or bank action is performed.

The AML training experiment and the AgentApp review workflow are separate components. Nebius was verified for review inference; the training run took place locally.

## Measured experiment

Sources: [results CSV](results/results.csv), [results methodology and caveats](results/README.md), and the merged model work in commit `e74bc0a`.

The CSV field `pr_auc` reports average precision, not accuracy. Rounded values from the merged experiment:

| Fictional group | Local AP | Federated AP | Pooled AP | Federated minus local |
|---|---:|---:|---:|---:|
| Americas | 0.00158 | 0.00134 | 0.00156 | -0.00024 |
| APAC | 0.54506 | 0.45287 | 0.09867 | -0.09219 |
| EMEA | 0.11430 | 0.23124 | 0.14786 | +0.11694 |
| India | 0.05831 | 0.37150 | 0.29370 | +0.31319 |
| Small group | 0.59351 | 0.37885 | 0.42878 | -0.21466 |

**The result is mixed:** federated training improved average precision for India and EMEA and reduced it for the other three groups. This single run does not establish a general federated advantage or statistical significance. Earlier five-round experiments in the handoff folders are separate artifacts.

## Demo and code

- [Event demo](docs/event-demo/index.html): presentation of the merged experiment.
- [Flower AgentApp](src/connectmesh-evidence-review/README.md): review workflow and operator instructions.
- [Event alignment](docs/EVENT_ALIGNMENT.md): event-facing scope.
- [Training application](src/model/flower_app/README.md): training instructions.

To view the event demo from a repository checkout:

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory docs/event-demo
```

Open http://127.0.0.1:8766 in a browser. This serves existing results; it does not start training or agent workers. Choose another port if 8766 is already occupied.

## Nebius configuration

The demonstrated model is `dedicated/flowerai/Kimi-K2.7-Code-1OUHWL`, using the organizer-provided Token Factory Responses endpoint:

`https://api.tokenfactory.tf-ca1.nebius.com/v1/responses`

Worker configuration uses `FLWR_MODEL_API_ENDPOINT` and `FLWR_MODEL_API_KEY`. Keep credentials outside source control and enter them privately. Updating a key in a separate API test does not update a running worker's environment; workers must be restarted with the corrected configuration. Access to the event endpoint is subject to organizer provisioning.

## Limits and next validation

- Team-provided IBM HI-Small synthetic data; original provenance has not been independently audited here. Regions are fictional bank-ID groupings, not actual geographic deployments.
- Five training client processes on one laptop are not five securely isolated bank servers. Federated model updates can leak information; federated learning alone is not a privacy guarantee. The pooled comparison intentionally combines records.
- One run, limited positive examples, and no uncertainty estimates. Repeat across seeds and temporal splits before drawing broader conclusions.
- Recall at the reported false-positive rate is a retrospective test ROC statistic, not a validated deployment threshold.
- No demonstrated real-world money-laundering prevention, production readiness, regulatory compliance, or novelty claim.
- Complete and retain a two-worker SuperGrid reply trace before describing distributed agent review as demonstrated.

## Team and contribution

Darsh: model/backend; Musa: data; Sahan: evaluation; Adam and Franklyn: Flower/frontend; Franklyn: PM/pitch.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance. Historical planning documents describe earlier training-only scope; the user-authorized event integration adds the separate AgentApp evidence-review workflow. Never alter data partitions or reported results to manufacture a favorable comparison.
