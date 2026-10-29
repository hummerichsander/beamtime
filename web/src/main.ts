// Boot: theme, project meta, live updates, routing, then the shell.

import { render } from "preact";
import { html } from "htm/preact";

import { busy, connect, post } from "./api.ts";
import { applyTheme, mode, pair } from "./bt/index.ts";
import { listen, rendering } from "./router.ts";
import { App } from "./shell/app.ts";
import { meta } from "./shell/ui.ts";
import { installTips } from "./ui/tip.ts";
import "./styles/index.css";

listen();
if (rendering) {
  // a still page for screenshots: the theme the renderer asks for, no live updates.
  const theme = new URLSearchParams(location.search).get("theme");
  if (theme === "light" || theme === "dark") mode.value = theme;
  document.documentElement.classList.add("rendering");
  (window as any).__btBusy = () => busy.n;
} else {
  connect();
}
installTips();
post("meta").then((m) => {
  meta.set(m);
  pair.set(m.theme);
  applyTheme();
});
render(html`<${App} />`, document.getElementById("app")!);
