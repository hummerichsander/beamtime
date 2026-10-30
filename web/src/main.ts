// Boot: theme, project meta, live updates, routing, then the shell.

import { render } from "preact";
import { html } from "htm/preact";

import { busy, connect, post } from "./api.ts";
import { mode } from "./bt/index.ts";
import { listen, rendering } from "./router.ts";
import { App } from "./shell/app.ts";
import { applyMeta } from "./shell/settings.ts";
import { installTips } from "./ui/tip.ts";
import "./styles/index.css";

listen();
if (rendering) {
  // a still page for screenshots: the theme the renderer asks for, no live updates.
  const theme = new URLSearchParams(location.search).get("theme");
  if (theme === "light" || theme === "dark") mode.value = theme;
  document.documentElement.classList.add("rendering");
  (window as any).__btBusy = () => busy.n;
}
installTips();
const first = post("meta").then((m) => {
  // the renderer's theme wins over the project's mode.
  if (rendering) m = { ...m, settings: { ...m.settings, theme_mode: mode.value } };
  applyMeta(m);
  return m;
});
// a server restarted with a rebuilt frontend (serve --watch): the page loads the new one.
if (!rendering) {
  connect(async () => {
    const [was, now] = await Promise.all([first, post("meta")]);
    if (was.bundle !== now.bundle) location.reload();
    else applyMeta(now);
  });
}
render(html`<${App} />`, document.getElementById("app")!);
