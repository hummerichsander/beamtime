// Writes from the UI. Files are never changed: an edited note is a new note that supersedes
// the old one, an edited memory or proposal a new version. The author is the local account.

import { type Call, invalidate, post } from "../api.ts";

// a group's answers that a write below or at `group` makes stale.
function refresh(group: string, methods: string[]): void {
  invalidate((c: Call) => methods.includes(c.method) && (c.scope === "." || group === c.scope ||
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
