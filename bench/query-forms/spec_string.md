# Writing `where` conditions

A query selects runs with a `where` condition. It is written as one condition string, inside a
YAML view file:

```yaml
where: "run.status == finished and config.lr < 1e-3"
```

## Rules

- A condition compares a **field** with a **value**: `config.lr < 1e-3`.
- Operators:

| Operator | Meaning |
|---|---|
| `==`, `!=` | equal, not equal |
| `<`, `<=`, `>`, `>=` | comparisons |
| `in`, `not in` | value is in / not in a list: `config.warmup in [500, 1000]` |
| `has` | list field contains a value: `run.tags has baseline` |
| `exists`, `not exists` | field is present / absent: `config.optimizer.weight_decay exists` |
| `~` | string matches a pattern with `*` and `?`: `run.name ~ 'prompt-*'` |

- Conditions combine with `and`, `or` and `not`, and parentheses group them. `not` binds tightest,
  then `and`, then `or`: `a or b and c` means `a or (b and c)`.
- Values: numbers (`3`, `0.5`, `1e-3`), strings in single or double quotes (`'cosine'`), and
  simple words without quotes (`finished`, `adam`). Strings containing spaces or special
  characters must be quoted. Lists use brackets: `[500, 1000]`.

```yaml
where: "run.status == finished and (config.warmup == 500 or config.optimizer.name == adamw) and not run.tags has ablation"
```

- In YAML, put the whole condition in double quotes and use single quotes for strings inside it.
