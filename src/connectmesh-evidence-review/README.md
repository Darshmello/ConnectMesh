# ConnectMesh: collaborative evidence review on Flower SuperGrid

The event-facing product is a Flower AgentApp: a coordinator requests numerical review and methodological challenge from peer agents, reconciles their actual replies against measured evidence, and produces a human-reviewable conclusion. Five-bank federated training supplies the evidence; it is distinct from agent collaboration.

## Verified training evidence

Pinned main commit: `e74bc0a16dd028cb0f00284c4cf057c81bf002aa`.
The merged team experiment completed 20 rounds with five clients on a 16 GB RAM Mac. It does not require a new training run for this demo. Its CSV shows gains for EMEA and India, losses for the other three groups. Earlier Franklyn five-round artifacts remain separate. Average precision is not accuracy. Recall is a retrospective test ROC statistic, not a deployed threshold. Synthetic data and fictional bank groupings only.

## Event acceptance checks

- Run the custom AgentApp on SuperGrid.
- Capture actual numerical-review and methodological-review peer replies, with node IDs and final reconciliation. An online node list is not sufficient.
- Publish the reviewed AgentApp to Flower Hub and record the resulting public app URL.
- Submit the team details, short description and GitHub URL using the organizer's submission instructions.
- Describe Nebius only after a successful provider-backed inference is verified; local training did not run there.

## Operator steps

Keep the two SuperNode terminals running. From the AgentApp directory build with the pinned Flower 1.38.0 CLI, then start chat. Select `/federation @aizoya/connectmesh-review`, then `/load .`. Start a fresh review of the bundled 20-round experiment; do not reuse the previous five-round conclusion.

Prompt: Review the bundled merged 20-round ConnectMesh experiment. Request numerical review from node 1630853058512194484 and methodological challenge from node 2263943161430437337 using Grid tools. Collect both replies and reconcile them against the CSV. Report which regions improve or regress, actual responding node IDs, limitations, and one next validation experiment. Never invent a reply. Mark SOLO REVIEW if peer collaboration fails.

## Team and scope correction

Adam and Franklyn are two people working together on Flower and frontend. Franklyn also owns PM/pitch; Darsh owns model/backend, Musa data, Sahan evaluation. Historical README/PLAN/AGENTS statements excluding Flower AgentApp are superseded for this user-authorized event integration. Do not change partitions to manufacture gains or present shared-model performance as guaranteed.

Official challenge and submission instructions:
https://discuss.flower.ai/t/collaborative-agent-hackathon-stanford-ca-2026/1275

Training sources:
https://github.com/Darshmello/ConnectMesh/blob/e74bc0a16dd028cb0f00284c4cf057c81bf002aa/results/README.md
https://github.com/Darshmello/ConnectMesh/blob/e74bc0a16dd028cb0f00284c4cf057c81bf002aa/results/runs/2026-09-29_federated_5bank/run.log

## Observed runtime status — September 29, 2026, 5:22 PM Pacific

- Direct Nebius Kimi inference and two review requests succeeded. These used the same model with separate prompts, outside SuperGrid messaging.
- SuperGrid v0.3.2 run `791632745106363984` completed but reported **Missing replies: 2. Review incomplete.** This is not successful end-to-end collaboration.
- Earlier v0.2.0 worker logs show HTTP 401 from the model provider. The corrected key subsequently passed a direct test and the two-worker launcher restarted; replies after restart remain unverified.
- The v0.3.2 recovery coordinator uses deterministic dispatch. Do not describe that dispatch as a demonstrated model-selected orchestration step.
- Recovery versions installed on the operator Mac may differ from the code committed here. Read the actual run version and logs.
- Flower Hub publication remains unverified. No automatic bank action.

See the [repository README](../../README.md) for the measured comparison and current demo limitations.
