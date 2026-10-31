// The documentation site's behaviour: search (⌘K, /), the theme switch, the page menu on narrow
// screens and the current section in "On this page". No dependencies; search.json is the index.

(() => {
  const root = document.documentElement.dataset.root ?? "";
  const dialog = document.querySelector("dialog.palette");
  const input = dialog.querySelector("input");
  const list = dialog.querySelector(".palette-list");
  let entries = null;
  let results = [];
  let active = 0;

  async function load() {
    if (entries) return entries;
    try {
      entries = await (await fetch(`${root}search.json`)).json();
    } catch {
      entries = [];
    }
    return entries;
  }

  // the app's palette scoring: a substring ranks by position, else the letters in order.
  function score(query, text) {
    const q = query.toLowerCase();
    const t = text.toLowerCase();
    const at = t.indexOf(q);
    if (at >= 0) return 100 - Math.min(at, 50) - t.length / 100;
    let i = 0;
    let gaps = 0;
    for (const ch of t) {
      if (ch === q[i]) i++;
      else if (i > 0) gaps++;
      if (i === q.length) return 40 - Math.min(gaps, 39);
    }
    return 0;
  }

  function rank(query) {
    const words = query.trim().split(/\s+/).filter(Boolean);
    if (!words.length) return entries.filter((e) => !e.section).map((e) => ({ e, s: 0 }));
    const out = [];
    for (const e of entries) {
      let total = 0;
      for (const w of words) {
        // a word in the title or a heading counts more than one in the text; fuzzy only for headings.
        const head = Math.max(score(w, e.section), score(w, e.page)) * 2;
        const body = e.text.toLowerCase().includes(w.toLowerCase()) ? 60 : 0;
        const s = Math.max(head >= 80 ? head : head / 2, body);
        if (!s) {
          total = 0;
          break;
        }
        total += s;
      }
      if (total) out.push({ e, s: total + (e.section ? 0 : 5) });
    }
    return out.sort((a, b) => b.s - a.s).slice(0, 40);
  }

  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  function highlight(text, words) {
    let html = esc(text);
    for (const w of words) {
      if (w.length < 2) continue;
      const re = new RegExp(`(${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
      html = html.replace(re, "<mark>$1</mark>");
    }
    return html;
  }

  // the text around the first match, so the snippet shows why a section was found.
  function snippet(text, words) {
    const lower = text.toLowerCase();
    const at = Math.min(...words.map((w) => lower.indexOf(w.toLowerCase())).filter((i) => i >= 0), Infinity);
    if (!Number.isFinite(at) || at < 60) return text.slice(0, 180);
    return `…${text.slice(at - 50, at + 130)}`;
  }

  function draw() {
    const query = input.value;
    const words = query.trim().split(/\s+/).filter(Boolean);
    results = rank(query);
    active = Math.min(active, Math.max(results.length - 1, 0));
    if (!results.length) {
      list.innerHTML = `<li class="empty">Nothing matches “${esc(query)}”.</li>`;
      return;
    }
    let html = "";
    let last = null;
    results.forEach(({ e }, i) => {
      if (e.page !== last) html += `<li class="section" role="presentation">${esc(e.page)}</li>`;
      last = e.page;
      const label = e.section ? highlight(e.section, words) : `${highlight(e.page, words)} <span class="where">· page</span>`;
      html += `<li class="item" role="option" id="r${i}" data-i="${i}" aria-selected="${i === active}">` +
        `<span class="label">${label}</span><span class="snippet">${highlight(snippet(e.text, words), words)}</span></li>`;
    });
    list.innerHTML = html;
    input.setAttribute("aria-activedescendant", `r${active}`);
  }

  function select(i) {
    active = i;
    list.querySelectorAll("li.item").forEach((li) => li.setAttribute("aria-selected", String(Number(li.dataset.i) === i)));
    list.querySelector(`#r${i}`)?.scrollIntoView({ block: "nearest" });
    input.setAttribute("aria-activedescendant", `r${i}`);
  }

  function go(i) {
    const r = results[i];
    if (!r) return;
    dialog.close();
    location.href = root + r.e.url;
  }

  async function open(query = "") {
    if (!dialog.open) dialog.showModal();
    input.value = query;
    active = 0;
    await load();
    draw();
    input.focus();
    input.select();
  }

  input.addEventListener("input", () => {
    active = 0;
    draw();
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") select(Math.min(active + 1, results.length - 1));
    else if (e.key === "ArrowUp") select(Math.max(active - 1, 0));
    else if (e.key === "Enter") go(active);
    else return;
    e.preventDefault();
  });
  list.addEventListener("click", (e) => {
    const li = e.target.closest("li.item");
    if (li) go(Number(li.dataset.i));
  });
  list.addEventListener("pointermove", (e) => {
    const li = e.target.closest("li.item");
    if (li && Number(li.dataset.i) !== active) select(Number(li.dataset.i));
  });
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) dialog.close();
  });
  document.querySelector(".search").addEventListener("click", () => open());
  document.addEventListener("keydown", (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName ?? "");
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      dialog.open ? dialog.close() : open();
    } else if (e.key === "/" && !typing && !dialog.open) {
      e.preventDefault();
      open();
    }
  });
  if (!/Mac|iPhone|iPad/.test(navigator.platform)) document.querySelector(".search kbd").textContent = "Ctrl K";
  const q = new URLSearchParams(location.search).get("q");
  if (q !== null) open(q);

  // the theme: system, light or dark, remembered in this browser.
  const modeButton = document.querySelector(".mode");
  const modes = ["system", "light", "dark"];
  const current = () => document.documentElement.dataset.mode ?? "system";
  const showMode = () => {
    modeButton.dataset.mode = current();
    modeButton.setAttribute("aria-label", `Theme: ${current()}`);
    modeButton.title = `Theme: ${current()}`;
  };
  modeButton.addEventListener("click", () => {
    const next = modes[(modes.indexOf(current()) + 1) % modes.length];
    if (next === "system") delete document.documentElement.dataset.mode;
    else document.documentElement.dataset.mode = next;
    try {
      next === "system" ? localStorage.removeItem("beamtime-docs-mode") : localStorage.setItem("beamtime-docs-mode", next);
    } catch {}
    showMode();
  });
  showMode();

  // the page menu on narrow screens.
  const docs = document.querySelector(".docs");
  const menu = document.querySelector(".menu");
  menu.addEventListener("click", () => {
    const openNav = !docs.classList.contains("nav-open");
    docs.classList.toggle("nav-open", openNav);
    menu.setAttribute("aria-expanded", String(openNav));
  });
  document.querySelector(".docs-main").addEventListener("click", () => {
    docs.classList.remove("nav-open");
    menu.setAttribute("aria-expanded", "false");
  });

  // "On this page" marks the section being read.
  const links = [...document.querySelectorAll(".toc a")];
  if (links.length && "IntersectionObserver" in window) {
    const heads = links.map((a) => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
    const mark = () => {
      let currentHead = heads[0];
      for (const h of heads) if (h.getBoundingClientRect().top < 120) currentHead = h;
      links.forEach((a) => a.classList.toggle("current", a.hash === `#${currentHead.id}`));
    };
    addEventListener("scroll", mark, { passive: true });
    mark();
  }
})();
