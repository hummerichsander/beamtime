# Mark

Beamtime's mark: three slanted strokes, `///`, in `accent`. It names the product in the top bar and the favicon; it is a brand sign, never a status sign.

- Two poses. **Rest**: the three strokes evenly spaced. **Gathered**: the middle stroke 2 and the right one 4 units to the left, so the three sit close together.
- Motion, "gather left": on hover and once on page load the middle and right strokes move to the gathered pose and back (420ms each way, ease in-out). Under `prefers-reduced-motion` they jump to the pose on hover and there is no load motion.
- Sizes: 16px in the top bar, with the 24 `viewBox` kept; larger only on a page that shows the product (about, empty app). Always in `accent`, never recolored by a state.
- The favicon is the rest pose in `accent` (light and dark). `favicon-live.svg` shows the gathered pose and loops gathered, rest, gathered every 2.8s in browsers that animate SVG icons; where they don't, the gathered pose stays. Both are generated from the tokens by `scripts/build-tokens`.
- Decorative: `aria-hidden`; the product name next to it carries the meaning.

## Markup

```html
<div style="display:flex;gap:24px;align-items:center"><svg class="mark" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 19.5 L9.5 4.5"/><path class="mark-2" d="M8.5 19.5 L15.5 4.5"/><path class="mark-3" d="M14.5 19.5 L21.5 4.5"/></svg><svg class="mark gathered" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 19.5 L9.5 4.5"/><path class="mark-2" d="M8.5 19.5 L15.5 4.5"/><path class="mark-3" d="M14.5 19.5 L21.5 4.5"/></svg></div>
```

## In the app

`Mark` in `web/src/ui/mark.ts`, in the top bar.
