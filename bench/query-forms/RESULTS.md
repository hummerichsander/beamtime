# Object form vs string form for `where` conditions

Question: do agents write query conditions more reliably as strings
(`config.lr < 1e-3 and run.status == finished`) or as YAML objects (`config.lr: {lt: 1.0e-3}`)?

## Setup

- 20 tasks (`tasks.md`) from simple equality to negated nested conditions, list membership, globs,
  windowed metric statistics, a config key containing a dot, and a value with spaces.
- One shared field reference (`context.md`) and two specs of equal depth (`spec_object.md`,
  `spec_string.md`).
- Fresh agents saw only the field reference, the tasks and one spec. 2 forms × 2 models (Sonnet,
  Haiku) × 2 repetitions = 8 agents, 160 answers.
- `score.py` parses each answer as a view would (PyYAML, then the condition), normalizes it to a
  canonical boolean tree (negations pushed to the leaves, `in` expanded, AND/OR flattened and
  sorted) and compares meaning with a reference. It also reports answers that are only correct after
  converting numeric strings to numbers (the PyYAML `1e-3`-is-a-string trap).
- Negative controls: a flipped operator and a `1e-3` written in YAML were both detected.

## Results

| | Sonnet | Haiku |
|---|---|---|
| Object form | 20/20, 20/20 | 20/20, 20/20 |
| String form | 20/20, 20/20 | 20/20, 20/20 |

- **No difference in correctness.** All 160 answers had the intended meaning, in both forms and with
  both models, including the hard cases (De Morgan in t20, the dotted config key in t18).
- **No meaningful difference in length**: 57 characters on average for the object form, 52 for the
  string form.
- **The YAML number trap did not occur**, because every object-form agent copied the spec's
  `1.0e-3` notation. Agents writing from memory instead of a spec would likely write `1e-3`; the
  validator must convert numeric strings on numeric fields.

## Conclusion

With a clear spec, the form does not matter for agents. The choice can rest on other grounds: one
canonical form, schema validation, and no second parser.
