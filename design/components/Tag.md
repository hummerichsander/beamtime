# Tag

A one- or two-word qualifier next to a title or statement, in `small`, tinted 10% of its own tone.

- Tones: `good`, `bad`, `warn`, `accent`, `muted`. Not for status (use Sym) or counts.

## Markup

```html
<div style="display:flex;gap:8px"><span class="tag small tone-warn">provisional</span><span class="tag small tone-muted">seed 3</span><span class="tag small tone-accent">proposed</span><span class="tag small tone-bad">invalid</span></div>
```

## In the app

`Tag` in `web/src/ui/primitives.ts`.
