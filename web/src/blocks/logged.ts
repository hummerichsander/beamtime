// Logged data: `images` and `text` of a data key, from the run's files.

import { html } from "htm/preact";

import { useData, type Node } from "../bt/index.ts";
import { step } from "../bt/fmt.ts";
import { Notice, Panel } from "./common.ts";

export function Images({ node }: { node: Node }) {
  const result = useData("main");
  const entries: any[] = result.data?.entries ?? [];
  return html`<${Panel} title=${node.props.title} caption=${node.props.caption} result=${result}>
    ${result.data && !entries.length ? html`<${Notice}>No images logged.<//>` : null}
    <div class="images">
      ${entries.map(
        (e) => html`<figure key=${`${e.run}/${e.path}`}>
          <img src=${`/api/file/${e.run}/${e.path}`} alt=${e.caption ?? node.props.title} loading="lazy" />
          <figcaption>step ${step(e.step)}${e.caption ? ` · ${e.caption}` : ""}</figcaption>
        </figure>`,
      )}
    </div>
  <//>`;
}

export function Text({ node }: { node: Node }) {
  const result = useData("main");
  const entries: any[] = result.data?.entries ?? [];
  return html`<${Panel} title=${node.props.title} caption=${node.props.caption} result=${result}>
    ${result.data && !entries.length ? html`<${Notice}>No text logged.<//>` : null}
    ${entries.map(
      (e) => html`<div class="text-entry" key=${`${e.run}/${e.step}`}>
        <div class="muted small">step ${step(e.step)}${e.caption ? ` · ${e.caption}` : ""}</div>
        <pre>${e.text ?? ""}</pre>
      </div>`,
    )}
  <//>`;
}
