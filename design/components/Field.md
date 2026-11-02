# Field

A label in `small` `muted` above an input with a `border` edge; `accent` while focused; an error below in `bad`.

- Search fields lead with the search icon. Placeholders say what can be typed, not "Search…".
- Errors say what is wrong, right under the field.

## Markup

```html
<div style="display:grid;gap:16px;max-inline-size:360px"><label class="field small"><span class="field-label">Filter runs</span><span class="input body"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="m21 21-4.34-4.34"/><circle cx="11" cy="11" r="8"/></svg><input placeholder="name, status or config" aria-label="Filter runs"></span></label><label class="field small"><span class="field-label">Aggregate</span><span class="input body"><select><option>over seeds</option></select></span></label><label class="field small"><span class="field-label">Step range</span><span class="input body"><input value="2000 – 100"></span><span class="field-hint error">The end comes before the start.</span></label></div>
```

## In the app

`Field` in `web/src/ui/primitives.ts`.

- Added: `.field.inline` (label beside the control), and bare `.input` where a grid already labels the control.
