// A page's view: its body, where it comes from (the default, a version, a draft), "Save as view",
// and the version history with a YAML diff and two versions side by side.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";
import { useMemo, useState } from "preact/hooks";

import { invalidate, post, useCall } from "../api.ts";
import { Block } from "../blocks/index.ts";
import { LabelCtx, Notice, rows } from "../blocks/common.ts";
import { diffLines, fold } from "../bt/diff.ts";
import { ago, versionTime } from "../bt/fmt.ts";
import { runColors, useTheme, ViewCtx, type Node } from "../bt/index.ts";
import { labelOf } from "../bt/labels.ts";
import { changed, update, usePrefs } from "../bt/prefs.ts";
import { editText, fresh, upgradeView } from "../bt/writes.ts";
import { groupUrl, navigate, route } from "../router.ts";
import { useStore } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import { Button, Field, Section } from "../ui/primitives.ts";
import * as calls from "./calls.ts";
import { snapshot } from "../snapshot.ts";

// a compiled view with what its blocks share: run colors and names, and the view's metrics.
export function ViewBody(props: { path: string; view: any; before?: ComponentChildren; plain?: boolean }) {
  const ids = useCall(calls.runIds(props.path));
  const theme = useTheme();
  const runs = rows(ids.data);
  const colors = useMemo(() => runColors(runs.map((r) => r["run.id"]), theme), [ids.data, theme]);
  const names = useMemo(() => new Map(runs.map((r) => [r["run.id"], r["run.name"] ?? r["run.id"]])), [ids.data]);
  const shell = props.plain ? "view plain" : "sections view";
  if (!props.view) {
    return html`<div class=${shell}>${props.before}
      ${props.plain
        ? html`<div class="skeleton late" style="block-size: 320px"></div>`
        : html`<${Section} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;
  }
  const value = { path: props.path, colors, names, metrics: props.view.metrics ?? {} };
  const root: Node = props.view.view;
  if (props.plain) return html`<div class=${shell}><${ViewCtx.Provider} value=${value}><${Block} node=${root} /><//></div>`;
  // every top-level block sits in its own Section; layouts below it stay inside.
  const blocks = root.block === "section" && !root.props.title ? root.children ?? [] : [root];
  return html`<div class=${shell}>${props.before}
    <${ViewCtx.Provider} value=${value}>
      ${blocks.map((b) => {
        const label = labelOf(b);
        return html`<${Section} key=${b.id} label=${label}><${LabelCtx.Provider} value=${label}><${Block} node=${b} /><//><//>`;
      })}
    <//>
  </div>`;
}

// where the shown view comes from, its history, and saving the viewer's charts as a version.
export function ViewSource(props: { path: string; view: any }) {
  if (snapshot) return html`<div class="view-source small"><${Icon} name="clock" size=${14} />
    <span>a snapshot of <b>${props.path === "." ? "the log dir" : props.path}</b>, taken ${new Date(snapshot.taken * 1000).toLocaleString()};
      curves at ${snapshot.points === "all" ? "every logged point" : `${snapshot.points} points`}; Beamtime ${snapshot.version}</span></div>`;
  const v = props.view;
  const r = useStore(route);
  const old = r.page === "group" && r.version;
  const history = v.versions
    ? html`<a href=${groupUrl(props.path, { history: true })}><${Icon} name="history" size=${14} /> history (${v.versions})</a>`
    : null;
  let what;
  switch (v.source) {
    case "draft":
      what = html`draft <b>${v.draft}</b>`;
      break;
    case "view":
      what = html`${v.title ? html`<em>${v.title}</em> · ` : null}saved ${ago(versionTime(v.version))} by ${v.author ?? "unknown"}`;
      break;
    default:
      what = html`the built-in view`;
  }
  return html`<div class="view-source small">
    <${Icon} name="layout" size=${14} /><span>${what}</span>
    ${old ? html`<a href=${groupUrl(props.path)}>an older version · show the current one</a>` : null}
    ${history}
    ${v.outdated?.length && !old ? html`<${Upgrade} path=${props.path} outdated=${v.outdated} />` : null}
    ${v.source === "draft" || old
      ? null
      : html`<${AddText} path=${props.path} />
        <${SaveView} path=${props.path} view=${v} />`}
  </div>`;
}

// library blocks with newer versions than the view is pinned to; updating saves a new version.
function Upgrade(props: { path: string; outdated: { name: string }[] }) {
  const [error, setError] = useState<string | null>(null);
  const names = props.outdated.map((o) => o.name).join(", ");
  const run = async () => {
    setError(null);
    try {
      await upgradeView(props.path);
    } catch (err) {
      setError((err as Error).message.split("\n")[0]);
    }
  };
  return html`<button type="button" class="link small" onClick=${run}
      data-tip=${`A newer version of ${names} exists; update re-pins this view to it (a new version)`}>
      <${Icon} name="update" size=${14} /> update ${names}</button>
    ${error ? html`<span class="bad-text small">${error}</span>` : null}`;
}

function AddText(props: { path: string }) {
  const [error, setError] = useState<string | null>(null);
  const add = async () => {
    setError(null);
    try {
      fresh.set(await editText(props.path, null, ""));
    } catch (err) {
      setError((err as Error).message);
    }
  };
  return html`<button type="button" class="link small" onClick=${add} data-tip="Add a text panel at the top of this page's view">
      <${Icon} name="file-text" size=${14} /> add text</button>
    ${error ? html`<span class="bad-text small">${error}</span>` : null}`;
}

// the viewer's chart settings and added charts, the title and the finding, as a new version.
function SaveView(props: { path: string; view: any }) {
  const prefs = usePrefs(props.path);
  const edited = changed(prefs);
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(props.view.title ?? "");
  const [finding, setFinding] = useState(props.view.finding ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (!edited && !open) return null;
  const save = async (e: Event) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const keep = { charts: prefs.charts, view: prefs.view, added: prefs.added, order: prefs.order, spans: prefs.spans };
      await post("save_view", { path: props.path, prefs: keep, title, finding });
      // the saved view now shows what the viewer had set; their own settings would repeat it.
      update(props.path, () => ({ view: {}, charts: {}, added: [], order: {}, spans: {} }));
      invalidate((c) => ["view", "view_history", "summary"].includes(c.method) && c.scope === props.path);
      setOpen(false);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };
  if (!open) {
    return html`<${Button} icon="save" class="save-view" onClick=${() => setOpen(true)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`;
  }
  return html`<form class="save-form" onSubmit=${save}>
    <${Field} label="Title"><input value=${title} onInput=${(e: Event) => setTitle((e.target as HTMLInputElement).value)} /><//>
    <${Field} label="Finding"><input value=${finding} placeholder="the key result in one sentence"
        onInput=${(e: Event) => setFinding((e.target as HTMLInputElement).value)} /><//>
    <div class="save-actions">
      <${Button} type="submit" icon=${busy ? "hourglass" : "save"} disabled=${busy}>${busy ? "Saving…" : "Save as view"}<//>
      <${Button} icon="x" kind="quiet" onClick=${() => setOpen(false)}>Cancel<//>
      ${error ? html`<span class="bad-text small">${error}</span>` : null}
    </div>
  </form>`;
}

export function History(props: { path: string }) {
  const result = useCall(calls.history(props.path));
  const entries: any[] = result.data?.entries ?? [];
  const [picked, setPicked] = useState<string[] | null>(null);
  const pair = picked ?? entries.slice(0, 2).map((e) => e.version).reverse();
  const toggle = (v: string) => {
    const next = pair.includes(v) ? pair.filter((x) => x !== v) : [...pair, v].slice(-2);
    setPicked(next.sort());
  };
  if (result.status === "error") return html`<${Notice} kind="error">${result.error}<//>`;
  return html`<section class="history">
    <h2 class="history-title heading"><${Icon} name="history" size=${16} /> View history</h2>
    ${result.data && !entries.length ? html`<${Notice}>No saved view yet; the page shows the built-in view.<//>` : null}
    <ol class="versions">
      ${entries.map(
        (e, i) => html`<li key=${e.version} class=${pair.includes(e.version) ? "picked" : ""}>
          <label><input type="checkbox" checked=${pair.includes(e.version)} onChange=${() => toggle(e.version)} />
            <span class="num muted" data-tip=${e.version}>${ago(e.time)}</span>
            <b>${e.title ?? "untitled"}</b><span class="muted">${e.author ?? ""}</span>
            ${e.message ? html`<span>${e.message}</span>` : null}</label>
          <a href=${i === 0 ? groupUrl(props.path) : groupUrl(props.path, { version: e.version })}
            onClick=${(ev: MouseEvent) => {
              ev.preventDefault();
              navigate(i === 0 ? groupUrl(props.path) : groupUrl(props.path, { version: e.version }));
            }}>${i === 0 ? "current" : "show"}</a>
        </li>`,
      )}
    </ol>
    ${pair.length === 2 ? html`<${Compare} path=${props.path} a=${pair[0]} b=${pair[1]} />` : null}
  </section>`;
}

function Compare(props: { path: string; a: string; b: string }) {
  const show = (version: string) => ({ method: "view_show", params: { group: props.path, version }, scope: props.path });
  const a = useCall(show(props.a)).data;
  const b = useCall(show(props.b)).data;
  const va = useCall(calls.view(props.path, props.a)).data;
  const vb = useCall(calls.view(props.path, props.b)).data;
  const lines = a && b ? fold(diffLines(a.yaml, b.yaml)) : [];
  return html`<div class="compare">
    <h3 class="block-title heading">Changes from ${ago(versionTime(props.a))} to ${ago(versionTime(props.b))}</h3>
    <pre class="diff code">${lines.map((l) =>
      l.kind === "skip"
        ? html`<div class="diff-skip">⋯ ${l.count} unchanged lines</div>`
        : html`<div class=${`diff-${l.kind}`}>${l.kind === "added" ? "+ " : l.kind === "removed" ? "− " : "  "}${l.text}</div>`,
    )}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${va?.title ?? props.a}</h3><${ViewBody} path=${props.path} view=${va} plain /></div>
      <div><h3 class="block-title heading">${vb?.title ?? props.b}</h3><${ViewBody} path=${props.path} view=${vb} plain /></div>
    </div>
  </div>`;
}
