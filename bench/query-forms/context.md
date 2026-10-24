# Beamtime: fields available in this log dir

Beamtime is an experiment logger. A view or a CLI call selects runs with a `where` condition over
**fields**. Every field is a dotted path with a namespace.

## Run fields

| Field | Type | Values |
|---|---|---|
| `run.name` | string | e.g. `boosted-kaon-42`, `prompt-photon-7` |
| `run.status` | string | `running`, `finished`, `failed`, `killed`, `lost` |
| `run.tags` | list of strings | e.g. `baseline`, `ablation`, `resnet18` |
| `run.steps` | integer | number of steps logged so far |
| `run.duration_s` | number | seconds |

## Config fields

| Field | Type | Values |
|---|---|---|
| `config.lr` | number | 1e-5 … 1e-2 |
| `config.optimizer.name` | string | `adam`, `adamw`, `sgd` |
| `config.optimizer.weight_decay` | number | only present in some runs |
| `config.batch_size` | integer | 32 … 1024 |
| `config.warmup` | integer | 0, 500, 1000 |
| `config.seed` | integer | 0 … 4 |
| `config.model.n_layers` | integer | 6, 12, 24, 48 |
| `config.model.dropout` | number | 0.0 … 0.3 |
| `config.scheduler` | string | `cosine`, `cosine with restarts`, `linear` |
| `config["mixup.alpha"]` | number | a single config key whose name contains a dot (not nested) |

A config key whose name itself contains a dot is written with brackets and quotes:
`config["mixup.alpha"]`. Nested keys use dots: `config.optimizer.name`.

## Metric fields

Logged metrics: `train/loss`, `val/loss`, `val/acc`, `lr`, `grad_norm`.

A metric field is `metric.<key>.<stat>`, e.g. `metric.val/acc.max`. Statistics: `first`, `last`,
`ema_last` (smoothed last value), `min`, `max`, `mean`, `count`, `nonfinite` (number of NaN/Inf
values), `slope_last10pct`.

A statistic over a step window appends `[start:end]` (inclusive):
`metric.val/loss.mean[1000:2000]`.

## Proposal fields

| Field | Values |
|---|---|
| `proposal.check` | `pass`, `fail`, `pending` (computed from the proposal's predictions) |
| `proposal.verdict` | `confirmed`, `refuted`, `inconclusive` (written by a human or agent) |
