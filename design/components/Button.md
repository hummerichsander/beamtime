# Button

An action with an icon and a short label in `body` at 600, no fill: `accent` text, a thin edge in the text color on hover. `danger` is `bad` (inside a confirmation); `quiet` is `muted` for cancel and secondary actions.

- The icon leads and says what kind of action it is; the label says what happens ("Save as view").
- Where the icon alone is clear, use an IconButton with the label as tooltip instead.
- Few buttons: most actions are links, IconButtons or inline editing. One accent button per place.

## Markup

```html
<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><button type="button" class="button body"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="icon" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>Save as view</button><button type="button" class="button body"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="icon" aria-hidden="true"><path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/></svg>Export</button><button type="button" class="button body" disabled><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="icon" aria-hidden="true"><path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/></svg>Saving…</button><button type="button" class="button body danger"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="icon" aria-hidden="true"><path d="M10 11v6"/><path d="M14 11v6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>Delete</button><button type="button" class="button body quiet"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="icon" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>Cancel</button></div>
```

## In the app

`Button` in `web/src/ui/primitives.ts`.
