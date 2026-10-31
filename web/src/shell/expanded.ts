// The page's dialog for an expanded chart: any chart block, from the view or from a custom
// block's frame, shown at full size with the context of the view it came from.

import { html } from "htm/preact";
import { useEffect, useRef } from "preact/hooks";

import { Block } from "../blocks/index.ts";
import { expanded } from "../bt/host.ts";
import { ViewCtx, type Node } from "../bt/index.ts";
import { useStore } from "../state.ts";

export function ExpandedChart() {
  const shown = useStore(expanded);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = dialog.current;
    if (!d || !shown) return;
    d.showModal();
    const close = () => expanded.set(null);
    d.addEventListener("close", close);
    return () => d.removeEventListener("close", close);
  }, [shown]);
  if (!shown) return null;
  const node: Node = { ...shown.node, props: { ...shown.node.props, expanded: true } };
  const name = String(node.props.title ?? node.props.y ?? "Chart");
  return html`<dialog class="sheet wide chart-dialog" ref=${dialog} aria-label=${name} closedby="any">
    <${ViewCtx.Provider} value=${shown.view}><${Block} node=${node} /><//>
  </dialog>`;
}
