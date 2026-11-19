// Beamtime's mark, `///`: three slanted strokes that gather left on hover and once on load (design/components/Mark.md).

import { html } from "htm/preact";

export function Mark({ size = 16 }: { size?: number }) {
  return html`<svg class="mark" width=${size} height=${size} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M2.5 19.5 L9.5 4.5" /><path class="mark-2" d="M8.5 19.5 L15.5 4.5" /><path class="mark-3" d="M14.5 19.5 L21.5 4.5" />
  </svg>`;
}
