// A compact multi-select for long lists (metric keys): the chosen values as removable chips,
// and a search field that opens a filtered list. Arrows move, Enter toggles, Esc closes.

import { html } from "htm/preact";
import { useId, useRef, useState } from "preact/hooks";

import { Icon } from "./icons.ts";

export function MultiSelect(props: {
  options?: string[];
  // options under headings, in place of `options`; searching spans all of them.
  groups?: [string, string[]][];
  // what an option shows, where it isn't its value.
  labels?: Record<string, string>;
  value: string[];
  onChange: (value: string[]) => void;
  label: string;
  placeholder?: string;
  // one value at a time: choosing one reports it and closes the list.
  single?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const id = `ms-${useId()}`.replace(/:/g, "");
  const q = query.trim().toLowerCase();
  const text = (o: string) => props.labels?.[o] ?? o;
  const groups = (props.groups ?? [["", props.options ?? []]]).map(
    ([name, options]) => [name, options.filter((o) => !q || text(o).toLowerCase().includes(q))] as const,
  );
  const shown = groups.flatMap(([, options]) => options);
  const chosen = new Set(props.value);
  const toggle = (o: string) => {
    if (props.single) {
      props.onChange([o]);
      setOpen(false);
      setQuery("");
      return;
    }
    const next = chosen.has(o) ? props.value.filter((v) => v !== o) : [...props.value, o];
    if (next.length) props.onChange(next);
  };
  const onKey = (e: KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        setOpen(true);
        setActive(Math.min(shown.length - 1, active + 1));
        break;
      case "ArrowUp":
        setActive(Math.max(0, active - 1));
        break;
      case "Enter":
        if (open && shown[active]) toggle(shown[active]);
        break;
      case "Escape":
        if (!open) return;
        setOpen(false);
        // only the list closes, not the panel around it.
        e.stopPropagation();
        break;
      case "Backspace":
        if (query || props.single || props.value.length < 2) return;
        props.onChange(props.value.slice(0, -1));
        return;
      default:
        return;
    }
    e.preventDefault();
  };
  return html`<div class="multiselect" onFocusOut=${(e: FocusEvent) => {
      if (!(e.currentTarget as HTMLElement).contains(e.relatedTarget as Node)) setOpen(false);
    }}>
    <div class="ms-field input body" onClick=${() => input.current?.focus()}>
      ${props.single
        ? null
        : props.value.map((v) => html`<span class="ms-chip small" key=${v}>${text(v)}
            ${props.value.length > 1
              ? html`<button type="button" aria-label=${`Remove ${v}`} data-tip=${`Remove ${v}`} onClick=${(e: Event) => { e.stopPropagation(); toggle(v); }}>
                  <${Icon} name="x" size=${14} /></button>`
              : null}</span>`)}
      <input ref=${input} value=${query} placeholder=${props.placeholder ?? "Search"} aria-label=${props.label}
        role="combobox" aria-expanded=${open} aria-controls=${id} aria-autocomplete="list"
        onFocus=${() => setOpen(true)} onKeyDown=${onKey}
        onInput=${(e: Event) => {
          setQuery((e.target as HTMLInputElement).value);
          setActive(0);
          setOpen(true);
        }} />
    </div>
    ${open
      ? html`<ul class="ms-list small" id=${id} role="listbox" aria-multiselectable=${!props.single}>
          ${shown.length ? null : html`<li class="ms-empty">No match</li>`}
          ${groups.map(([name, options]) => html`
            ${name && options.length ? html`<li class="ms-group" role="presentation">${name}</li>` : null}
            ${options.map((o) => html`<li key=${o} role="option" aria-selected=${chosen.has(o)} class=${shown.indexOf(o) === active ? "active" : ""}
                onPointerDown=${(e: Event) => e.preventDefault()} onClick=${() => toggle(o)} onPointerEnter=${() => setActive(shown.indexOf(o))}>
              <span class="ms-tick">${chosen.has(o) ? html`<${Icon} name="check" size=${14} />` : null}</span>${text(o)}</li>`)}`)}
        </ul>`
      : null}
  </div>`;
}
