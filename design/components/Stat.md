# Stat

One number with a small label, no box: a count, the best or the last value over a group's runs.

- Label in `small` `muted`, value in `number`. Italic while a run is still changing it.
- Compact numbers (`3e-4`, `12.4k`), the full value in the tooltip.

## Markup

```html
<div class="stats"><div><div class="stat-label small">runs</div><div class="number">12</div></div><div><div class="stat-label small">best val/loss</div><div class="number">0.412</div></div><div><div class="stat-label small">last train/loss</div><div class="number live">0.538</div></div><div><div class="stat-label small">steps</div><div class="number">12.4k</div></div></div>
```

## In the app

`Stat` in `web/src/blocks/stat.ts`.

- A row of stats renders as `.stats`; each stat also has class `stat`, and `pending` while loading.
