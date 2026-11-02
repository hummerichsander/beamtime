# Notice

A message where something happened: an empty state, a warning or an error, marked by a short rule in the margin rather than a box.

- Text in `muted`; the rule in `line` (info), `warn` or `bad`, with the matching icon for warnings and errors.
- No notices for things that went right.

## Markup

```html
<div style="display:grid;gap:8px;max-inline-size:520px"><p class="notice body">No groups below.</p><p class="notice body warning"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon tone-warn" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg><span>3 runs are behind: the index is catching up.</span></p><p class="notice body error"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon tone-bad" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg><span>Query failed: unknown column metric.val/acc</span></p></div>
```

## In the app

`Notice` in `web/src/blocks/common.ts`.
