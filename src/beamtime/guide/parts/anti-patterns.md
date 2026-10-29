# Anti-patterns

`view_validate` reports those marked ✓.

| Mistake | Fix |
|---|---|
| ✓ more than about eight curves in one chart | `color: <field>`, `by: [<field>]`, `seeds: config.seed` |
| ✓ aggregating runs that differ in more than noise | add the other varying keys to `by`, or narrow with `where` |
| ✓ a chart without caption | say what it shows, what varies, how many runs |
| ✓ a field or key that no run logs | use the names `keys` lists; validation suggests the closest |
| ✓ a block without data in scope | check `from`, `where` and `depth`; remove the block |
| ✓ no finding | state the result in one sentence |
| strong smoothing that hides spikes | lower `smooth` |
| comparing runs of different length without saying so | a `steps` window, or say it in the caption |
| a finding stronger than the check | state what the check says |
| a chart where a table or a single number would do | `table` or `stat` |
| scatter of a final value against a hyperparameter with several seeds as separate points | `seeds: config.seed` |
| log scale over values that can be zero or negative | a linear scale |
