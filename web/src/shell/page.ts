// Pages: a group or run with its view, the /r/<id> redirect, and settings.

import { html } from "htm/preact";
import { useEffect } from "preact/hooks";

import { fetchCall, useCall } from "../api.ts";
import { Notice } from "../blocks/common.ts";
import { groupUrl, navigate, restoreScroll } from "../router.ts";
import { useStore } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import * as calls from "./calls.ts";
import { Header } from "./header.ts";
import { History, ViewBody, ViewSource } from "./views.ts";
import { meta, SHORTCUTS } from "./ui.ts";

export function GroupPage(props: { path: string; version?: string | null; draft?: string | null; history?: boolean }) {
  useEffect(() => {
    document.title = `${props.path === "." ? "local" : props.path} · Beamtime`;
  }, [props.path]);
  if (props.history) return html`<div class="page"><${Header} path=${props.path} /><${History} path=${props.path} /></div>`;
  return html`<div class="page">
    <${ViewPage} path=${props.path} version=${props.version ?? null} draft=${props.draft ?? null} />
  </div>`;
}

function ViewPage(props: { path: string; version: string | null; draft: string | null }) {
  const view = useCall(calls.view(props.path, props.version, props.draft));
  useEffect(() => {
    if (view.status === "ready") requestAnimationFrame(restoreScroll);
  }, [view.status === "ready"]);
  return html`
    <${Header} path=${props.path} finding=${view.data?.finding} />
    ${view.data ? html`<${ViewSource} path=${props.path} view=${view.data} />` : null}
    ${view.status === "error"
      ? unreachable(props.path, view.error)
        ? html`<${Notice} kind="warning">${view.error} The page fills in once the remote answers again.<//>`
        : html`<${Notice} kind="error">${view.error}<//>`
      : html`<${ViewBody} path=${props.path} view=${view.data} />`}`;
}

// a remote that doesn't answer is a state of the source, not an error of the page.
function unreachable(path: string, error: string | null): boolean {
  return path.startsWith("@") && /is unreachable since/.test(error ?? "");
}

export function RunRedirect(props: { id: string }) {
  useEffect(() => {
    fetchCall(calls.view(props.id))
      .then((v) => navigate(groupUrl(v.path), { replace: true }))
      .catch(() => {});
  }, [props.id]);
  const view = useCall(calls.view(props.id));
  if (view.status === "error") return html`<div class="page"><${Notice} kind="error">${view.error}<//></div>`;
  return html`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`;
}
