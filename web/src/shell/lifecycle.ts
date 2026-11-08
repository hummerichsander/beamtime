// What a run's lifecycle left behind, for its details and the drawer: the code it ran, where it was
// copied from, its checkpoints, and the uncommitted changes (fetched only when opened).

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";
import { useState } from "preact/hooks";

import { useCall } from "../api.ts";
import { runUrl } from "../router.ts";
import { Disclosure, IconButton, Tag } from "../ui/primitives.ts";
import * as calls from "./calls.ts";

// the page of a commit on GitHub or GitLab, from the ssh or https remote the run recorded; any other host has none.
export function commitUrl(remote: string | null | undefined, commit: string): { host: string; url: string } | null {
  const url = /^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(remote ?? "");
  const scp = /^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(remote ?? "");
  const [, host, path] = url ?? scp ?? [];
  if (!host || !path) return null;
  if (host === "github.com") return { host: "GitHub", url: `https://github.com/${path}/commit/${commit}` };
  if (host === "gitlab.com" || host.startsWith("gitlab.")) return { host: "GitLab", url: `https://${host}/${path}/-/commit/${commit}` };
  return null;
}

// the rows a run page lists beyond its basics: only what is known.
export function lifecycleRows(card: any): [string, ComponentChildren][] {
  const { git, copied_from: from } = card.run;
  const rows: [string, ComponentChildren][] = [];
  if (git?.commit) rows.push(["code", html`<${Code} git=${git} />`]);
  if (from) {
    rows.push(["copied from", html`<a href=${runUrl(from.id)} data-tip=${`${from.id}, ${from.at}`}>${from.path ?? from.id}</a>`]);
  }
  if (card.checkpoints?.length) {
    rows.push(["checkpoints", html`${card.checkpoints.map((ck: any) => html`<${Checkpoint} key=${ck.name} ck=${ck} />`)}`]);
  }
  return rows;
}

function Code({ git }: { git: any }) {
  const link = commitUrl(git.remote, git.commit);
  return html`<span>${git.commit.slice(0, 10)}${git.branch ? html` on ${git.branch}` : null}
    ${git.dirty ? html` <${Tag} tone="warn" tip="Uncommitted changes when the run started">dirty<//>` : null}
    ${link ? html` · <a href=${link.url} target="_blank" rel="noopener noreferrer">${link.host}</a>` : null}</span>`;
}

// a missing file says why; there is no link to follow, only the place it was looked for.
function Checkpoint({ ck }: { ck: any }) {
  const copy = () => void navigator.clipboard?.writeText(ck.location);
  return html`<div class="checkpoint">
    <span class=${ck.exists ? "" : "muted"} data-tip=${ck.location ?? undefined}>${ck.name}</span>
    ${ck.exists ? null : html`<${Tag} tone="warn" tip=${ck.location ?? undefined}>missing<//> <span class="muted">${whyMissing(ck)}</span>`}
    ${ck.location ? html`<${IconButton} icon="copy" label=${`Copy the path of ${ck.name}`} onClick=${copy} />` : null}
  </div>`;
}

function whyMissing(ck: any): string {
  if (!ck.location) return "no location recorded";
  return ck.via === "origin" ? "not found where the source run kept it" : "not found at its recorded location";
}

// the changes the checkout had when the run started, which can be large: fetched on opening.
export function DiffViewer({ run, scope }: { run: string; scope: string }) {
  const [open, setOpen] = useState(false);
  const diff = useCall(open ? calls.diff(run, scope) : null);
  return html`<${Disclosure} summary="Uncommitted changes" onToggle=${setOpen}>
    ${diff.error ? html`<p class="muted small">${diff.error}</p>` : null}
    ${diff.data
      ? html`<pre class="log code diff">${String(diff.data.text)
          .split("\n")
          .map((line) => html`<span class=${lineTone(line)}>${line}\n</span>`)}</pre>`
      : open && !diff.error ? html`<div class="skeleton late" style="block-size: 80px"></div>` : null}
  <//>`;
}

function lineTone(line: string): string {
  if (line.startsWith("+++") || line.startsWith("---") || line.startsWith("@@")) return "muted";
  if (line.startsWith("+")) return "tone-good";
  return line.startsWith("-") ? "tone-bad" : "";
}
