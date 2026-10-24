# Writing `where` conditions

A query selects runs with a `where` condition. It is written in YAML, inside a view file:

```yaml
where:
  run.status: finished
  config.lr: {lt: 1.0e-3}
```

## Rules

- `where` is a **mapping from field to condition**. All entries must hold (AND).
- A **plain value** means equality: `run.status: finished`.
- A **condition mapping** applies operators: `config.lr: {lt: 1.0e-3}`. Several operators in one
  mapping must all hold: `config.lr: {ge: 1.0e-4, le: 1.0e-3}`.
- Operators:

| Operator | Meaning |
|---|---|
| `eq`, `ne` | equal, not equal |
| `lt`, `le`, `gt`, `ge` | <, <=, >, >= |
| `in`, `nin` | value is in / not in a list: `{in: [500, 1000]}` |
| `has` | list field contains a value: `run.tags: {has: baseline}` |
| `exists` | field is present (`true`) or absent (`false`): `{exists: true}` |
| `glob` | string matches a pattern with `*` and `?`: `{glob: "prompt-*"}` |

- Combinators, usable wherever a field entry can stand:
  - `any: [ ... ]`: at least one of the listed mappings holds (OR).
  - `all: [ ... ]`: all listed mappings hold (AND); useful to repeat a field.
  - `not: { ... }`: the mapping does not hold.

```yaml
where:
  run.status: finished
  any:
    - config.warmup: 500
    - config.optimizer.name: adamw
  not:
    run.tags: {has: ablation}
```

- Field names that contain special characters can be quoted as YAML keys, e.g.
  `'config["mixup.alpha"]': {gt: 0.1}`.
- Strings containing spaces or special characters should be quoted.
