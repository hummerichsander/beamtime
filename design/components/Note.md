# Note

A note written by a person or an agent: one line that opens to its text.

- The line: chevron, the note type as a Sym, the title in `heading`, `author · ago` in `small` `muted`.
- The body in `prose`, at most `measure` wide. Notes stay closed until clicked.

## Markup

```html
<div style="max-inline-size:600px"><article class="note"><div class="note-line"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon tone-muted" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg><span class="sym tone-accent" title='observation'><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg></span><span class="heading">Spikes vanish past 300 warmup steps</span><span class="note-meta small">claude · 2h ago</span></div><div class="note-body prose">All 9 runs with warmup ≥ 300 stay under a grad-norm of 10.</div></article><article class="note"><div class="note-line"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon tone-muted" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg><span class="sym tone-accent" title='idea'><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg></span><span class="heading">Try a cosine warmup instead of linear</span><span class="note-meta small">sander · 3d ago</span></div></article></div>
```

## In the app

`NoteItem` in `web/src/blocks/context.ts`.

- The chevron is a button (`.note-toggle`) and the title edits in place, so it is `.note-title.heading`.
