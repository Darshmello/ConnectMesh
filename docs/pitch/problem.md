# Problem

**First principles:** good models need data. The most valuable data (patient
records, bank transactions, phone keystrokes) can't be pooled onto one
server, because of law, privacy, or *competition*. Normal training requires
pooling data on one server — so all of it except your own goes unused.

**For banks specifically:** each bank's laundering model only ever sees that
bank's own laundering patterns. A bank can't hand its raw transactions to a
rival bank to improve fraud detection — that's illegal (privacy/data law)
and unwise (hands a competitor your transaction data). So five banks each
fight laundering alone, using a fifth of the pattern history that exists
between them.

**Why this is a consortium story, not one company's internal tooling:** the
incentive problem only exists between separate legal entities. That's also
why the right comparison set is Swift, Consilient, BIS Project Aurora and
Banking Circle (see `competitors.md`) — all multi-bank consortiums, not
internal bank tooling.

**What Flower does about it:** banks train one shared model together; each
bank's raw data stays on its own machine, only model updates are exchanged.
The model learns from every bank's laundering history without any bank's
data ever leaving its own server.

- [fill in] Cost of the status quo — use the "gain from joining" chart
  (federated PR-AUC minus local PR-AUC), especially for the smallest region,
  as the concrete number here once results are real.
- Regulatory specifics (why pooling is illegal, not just unwise) go in
  `laws.md` — cite EU / India / China sources.
