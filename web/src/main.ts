// Boot: theme, project meta, live updates, routing, then the shell.

import { render } from "preact";
import { html } from "htm/preact";

import { connect, post } from "./api.ts";
import { applyTheme, pair } from "./bt/index.ts";
import { listen } from "./router.ts";
import { App } from "./shell/app.ts";
import { meta } from "./shell/ui.ts";
import { installTips } from "./ui/tip.ts";
import "./styles/index.css";

listen();
connect();
installTips();
post("meta").then((m) => {
  meta.set(m);
  pair.set(m.theme);
  applyTheme();
});
render(html`<${App} />`, document.getElementById("app")!);
