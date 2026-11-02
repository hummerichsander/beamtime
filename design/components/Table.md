# Table

Runs as rows: `line` hairlines between them, a light accent tint on hover, the selected run tinted stronger.

- The first column is the run with its swatch: its color and its line style, as in the charts. Numbers right-aligned in tabular figures; the best value per column bold.
- Headers in `small` `muted`, naming the metric (`val/loss`), not the aggregate.
- A numbered `caption` below: "**Table 1.** What it shows."

## Markup

```html
<table class="runs"><thead><tr class="small"><th>run</th><th>status</th><th class="num">lr</th><th class="num">val/loss</th><th>created</th></tr></thead><tbody><tr><td><span class="swatch run-1"></span><a href="#">warmup-100</a></td><td><span class="sym tone-bad"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg><span class=small>failed</span></span></td><td class="num">1e-3</td><td class="num">—</td><td class="muted">2h ago</td></tr><tr><td><span class="swatch run-2"></span><a href="#">warmup-300</a></td><td><span class="sym tone-good"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span class=small>finished</span></span></td><td class="num">1e-3</td><td class="num">0.431</td><td class="muted">2h ago</td></tr><tr class=selected><td><span class="swatch run-3"></span><a href="#">warmup-500</a></td><td><span class="sym tone-good"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span class=small>finished</span></span></td><td class="num">1e-3</td><td class="num best">0.412</td><td class="muted">2h ago</td></tr><tr><td><span class="swatch run-4"></span><a href="#">warmup-500-s2</a></td><td><span class="sym tone-accent"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="12" r="10"/></svg><span class=small>running</span></span></td><td class="num">1e-3</td><td class="num">0.418</td><td class="muted">2h ago</td></tr><tr><td><span class="swatch run-5"></span><a href="#">cosine-300</a></td><td><span class="sym tone-good"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span class=small>finished</span></span></td><td class="num">1e-3</td><td class="num">0.425</td><td class="muted">2h ago</td></tr><tr><td><span class="swatch run-6"></span><a href="#">cosine-500</a></td><td><span class="sym tone-warn"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><rect width="18" height="18" x="3" y="3" rx="2"/></svg><span class=small>killed</span></span></td><td class="num">1e-3</td><td class="num">0.47</td><td class="muted">2h ago</td></tr></tbody></table><p class="caption"><b>Table 1.</b> Runs in this group; the best val/loss in bold.</p>
```

## In the app

`Table` in `web/src/blocks/table.ts`.

- Added: `.table-wrap` (scroll), sticky sorted headers, sparklines, and `.swatch-toggle`, the swatch's button that hides a run in charts.
- Cells are inset from the row's tint, and the wrap overhangs the column, so text still lines up down the page.
- A caption's number comes from a CSS counter: write `<b></b>`, with class `table-caption` on the caption.
