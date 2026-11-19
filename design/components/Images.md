# Images

The images a run logged under one key, as figures with a step scrubber: the head of a chart, a row of tiles, one slider under them.

- Tiles are square and keep one size (`object-fit: contain`, pixelated), on a `surface` panel with the radius token; the caption under a tile is `small` `muted` ("step 4000", then the logged caption).
- A run that logged nothing at the scrubbed step shows its latest earlier image at reduced opacity, with its own step in the caption.
- The scrubber is the system's range with a label to its right in `small` `muted`, tabular figures: "step 4000", or "epoch 12 · step 4000" when the page has a clock. It has one stop per logging; with fewer than two there is none.
- Tools on hover, as in a chart: a text toggle "by epoch" (accent when on), the download menu ("Latest image": the shown image logged last, one file; "All images (n)": every shown image) and expand.
- In the dialog the image fills the box, zooms under the pointer and pans by dragging; the tools add previous and next image, zoom out and in, and fit.

## Markup

```html
<figure class="chart" style="margin:0;inline-size:440px"><div class="chart-head"><b>samples</b></div><div style="display:flex;gap:12px"><figure style="margin:0"><div style="inline-size:96px;block-size:96px;border-radius:var(--radius);background:var(--surface)"></div><figcaption class="small muted">step 4000</figcaption></figure><figure style="margin:0"><div style="inline-size:96px;block-size:96px;border-radius:var(--radius);background:var(--surface);opacity:0.55"></div><figcaption class="small muted">step 3000</figcaption></figure></div><div style="display:flex;align-items:center;gap:12px;margin-block-start:12px"><input type="range" min="0" max="100" value="100" aria-label="Step" style="flex:1"><span class="small muted">epoch 12 · step 4000</span></div></figure>
```

## In the app

`Images` in `web/src/blocks/logged.ts` inside `ChartFrame`; the stops and labels are `web/src/bt/scrub.ts`, pan and zoom `web/src/bt/zoom.ts` (a CSS transform, no library). Styles in `web/src/styles/blocks.css` (`.scrubber`, `.zoom-box`).

- The scrubbed step is kept per page and block for the session, not in the URL; at the last stop the block follows a running run.
- Download saves the original files, not a re-encoded PNG; in the dialog "This image" replaces "Latest image".
- The dialog catches the wheel only inside the image, so the page never scrolls under it.
