// Writes from the UI. Files are never changed: an edited note is a new note that supersedes
// the old one, an edited memory or proposal a new version. The author is the local account.

import { type Call, invalidate, post } from "../api.ts";
import { Store } from "../state.ts";

// a group's answers that a write below or at `group` makes stale.
function refresh(group: string, methods: string[]): void {
  invalidate((c: Call) => methods.includes(c.method) && c.scope !== null && (c.scope === "." || group === c.scope ||
    group.startsWith(`${c.scope}/`) || c.scope.startsWith(`${group}/`)));  // prettier-ignore
}

const NOTE_ANSWERS = ["notes", "timeline", "groups", "check", "card", "memory_show", "status"];

export async function editNote(note: any, change: { description?: string; body?: string }): Promise<void> {
  const m = note.meta ?? {};
  await post("note_add", {
    group: note.group,
    type: note.type,
    description: change.description ?? note.description,
    body: change.body ?? note.body ?? "",
    supersedes: note.id,
    // the typed fields carry over: what it resolves, completes, cites and judges.
    resolves: m.resolves ?? [],
    completes: m.completes ?? [],
    evidence: m.evidence ?? [],
    ...(m.proposal ? { proposal: m.proposal, verdict: m.verdicts ?? {}, overall: m.overall ?? null } : {}),
  });
  refresh(note.group, NOTE_ANSWERS);
}

export async function addNote(group: string, type: string, description: string, body: string): Promise<void> {
  await post("note_add", { group, type, description, body });
  refresh(group, NOTE_ANSWERS);
}

export async function editMemory(group: string, body: string): Promise<void> {
  await post("memory_update", { group, body });
  refresh(group, ["memory_show", "status"]);
}

// a statement is edited as a new version of the proposal; frozen versions are not (see caller).
export async function editStatement(group: string, statement: string): Promise<void> {
  const shown = await post("proposal_show", { group });
  const doc = Object.fromEntries(
    Object.entries(shown.proposal ?? {}).filter(([k]) => !["schema", "author", "user", "supersedes"].includes(k)),
  );
  await post("proposal_set", { group, proposal: { ...doc, statement } });
  refresh(group, ["groups", "proposal_show", "check", "summary"]);
}

// deleting is the user's alone: the note and its earlier versions move to the trash.
export async function deleteNote(note: any): Promise<void> {
  await post("note_rm", { note: note.id });
  refresh(note.group, NOTE_ANSWERS);
}

// a run keeps its id; the name it shows is a new version.
export async function renameRun(run: string, scope: string, name: string): Promise<void> {
  await post("name", { run, name });
  refresh(scope, ["card", "runs", "groups", "summary", "series"]);
}

// a text panel of the page's view: added (id null), edited, or removed (empty text); each a version.
export async function editText(path: string, id: string | null, text: string): Promise<string> {
  const answer = await post("view_text", { path, id, text });
  invalidate((c: Call) => ["view", "view_history"].includes(c.method) && c.scope === path);
  return answer.id;
}

// re-pins the page's view to the newest versions of its library blocks.
export async function upgradeView(path: string): Promise<void> {
  await post("view_upgrade", { group: path });
  invalidate((c: Call) => ["view", "view_history"].includes(c.method) && c.scope === path);
}

// the text panel just added, which opens ready to type.
export const fresh = new Store<string | null>(null);

// a setting from the UI goes into the project's beamtime.yaml; the shell then reloads its meta.
export async function saveSetting(key: "theme" | "theme_mode" | "colormap" | "colormap_diverging" | "figure_style", value: unknown): Promise<any> {
  await post("set", { key, value });
  return post("meta");
}
