// Text written by agents or people, edited where it stands: click it, change it, and it saves
// when you leave the field or press Enter (⌘Enter in longer texts). Esc puts it back.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { Icon } from "./icons.ts";

export function Editable(props: {
  value: string;
  onSave: (value: string) => Promise<unknown>;
  label: string;
  multiline?: boolean;
  render?: (value: string) => ComponentChildren;
  // why it can't be edited, shown as its tooltip; editable when absent.
  locked?: string;
  placeholder?: string;
  class?: string;
  startEditing?: boolean;
  onCancel?: () => void;
}) {
  const [editing, setEditing] = useState(!!props.startEditing);
  const [draft, setDraft] = useState(props.value);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const field = useRef<HTMLTextAreaElement>(null);
  // Enter saves and closes the field, and closing it blurs it: save only once per edit.
  const closing = useRef(false);

  // a saved value shows until the refetched one arrives.
  useEffect(() => setSaving(null), [props.value]);
  useEffect(() => {
    if (!editing || !field.current) return;
    field.current.focus();
    // a field opened for a new text has its placeholder selected, to type over it.
    if (props.startEditing) field.current.select();
    else field.current.setSelectionRange(field.current.value.length, field.current.value.length);
  }, [editing]);

  const [explained, setExplained] = useState(false);
  const start = (e: MouseEvent | KeyboardEvent) => {
    if ((e.target as Element).closest("a, button, input, summary")) return;
    // a text that can't change says why when clicked, instead of ignoring the click.
    if (props.locked) return setExplained(true);
    e.preventDefault();
    setDraft(saving ?? props.value);
    setError(null);
    closing.current = false;
    setEditing(true);
  };
  const cancel = () => {
    closing.current = true;
    setEditing(false);
    setError(null);
    props.onCancel?.();
  };
  const save = async () => {
    if (closing.current) return;
    closing.current = true;
    const value = props.multiline ? draft.trim() : draft.replace(/\s*\n\s*/g, " ").trim();
    if (value === props.value.trim() || (!value && !props.multiline)) return cancel();
    setEditing(false);
    setSaving(value);
    try {
      await props.onSave(value);
    } catch (err) {
      setSaving(null);
      setDraft(value);
      setError((err as Error).message);
      closing.current = false;
      setEditing(true);
    }
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      return cancel();
    }
    // Enter that confirms an IME composition is not a save (keyCode 229 covers Safari's order).
    if (e.key !== "Enter" || e.isComposing || e.keyCode === 229) return;
    if (!props.multiline || e.metaKey || e.ctrlKey) {
      e.preventDefault();
      void save();
    }
  };

  if (editing) {
    return html`<div class=${`editable editing ${props.class ?? ""}`}>
      <textarea ref=${field} class="edit-field" value=${draft} aria-label=${props.label} placeholder=${props.placeholder}
        rows=${props.multiline ? Math.min(18, Math.max(4, draft.split("\n").length + 1)) : 1}
        onInput=${(e: Event) => setDraft((e.target as HTMLTextAreaElement).value)} onKeyDown=${onKey} onBlur=${save}></textarea>
      <span class="edit-hint">${props.multiline ? "⌘Enter saves" : "Enter saves"} · Esc cancels${error ? html` · <span class="bad-text">${error}</span>` : null}</span>
    </div>`;
  }
  const shown = saving ?? props.value;
  return html`<div class=${`editable${props.locked ? " locked" : ""}${saving !== null ? " saving" : ""} ${props.class ?? ""}`}
      tabindex=${0} role="button" aria-label=${props.locked ? `${props.label}: ${props.locked}` : `Edit ${props.label}`}
      data-tip=${props.locked} onClick=${start} onBlur=${() => setExplained(false)}
      onKeyDown=${(e: KeyboardEvent) => e.key === "Enter" && e.target === e.currentTarget && start(e)}>
    ${shown.trim() ? (props.render ? props.render(shown) : shown) : html`<span class="subtle">${props.placeholder ?? "Click to write"}</span>`}
    ${explained && props.locked ? html`<span class="edit-hint locked-why" role="status"><${Icon} name="lock" size=${12} /> ${props.locked}</span>` : null}
  </div>`;
}
