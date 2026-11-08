# Queries and fields

Blocks declare their queries implicitly: a block's props become a query over its scope (the page,
or `from`), narrowed by the view's `filters` and the block's `where`. The same queries are MCP
tools, so check a block's data with them before writing it.

## Fields (one value per run)

| Field | Meaning |
|---|---|
| `run.name`, `run.id`, `run.status`, `run.group`, `run.created_at`, `run.tags` | the run |
| `config.<key>` | a config value, e.g. `config.lr`, `config.model.depth` |
| `metric.<key>.<stat>` | a statistic of a metric's curve: `last`, `min`, `max`, `mean`, `first`, `count`; over a step window `metric.val/loss.mean[0:1000]` |
| `value.<key>` | a summary value logged once, e.g. `value.test/acc` |

Metric keys (`val/loss`) are used where a block plots a curve over steps (`line.y`,
`table.sparkline`); fields everywhere a block works with one value per run.

## where

`{field: value}` or `{field: {op: value}}` with `eq ne lt le gt ge in nin has exists glob`;
combine with `any: [...]` and `not: {...}`.

```yaml
where: {config.model: resnet18, metric.val/acc.max: {gt: 0.8}, run.status: {ne: failed}}
```

## Aggregation

- `seeds: config.seed` averages over seeds: one curve, point or row per combination of the other
  config keys.
- `by: [config.lr]` on `runs` gives one row per value, with `metric.<key>.<stat>` columns as mean,
  std and count: `runs --by config.lr --select metric.val/acc.last`.
- `by: [config.lr]` (line) draws the mean per value with a band (`band: minmax | std | stderr |
  none`).

## Tools to look before writing

`keys <group>` lists metrics, config keys with their values, data keys and tags; `runs <group>
--select ... --sort ...`; `series <group> -y val/loss --by config.lr`; `data <group> <key>`.
