# Setup wizard: decisions before the spec

Input for `docs/design/10-setup.md` and for `/plan-tickets` into `docs/plans/setup/`. The mockup
`docs/design/10-setup-mockup.html` is the agreed experience (open it in a browser; four scenarios,
each step's margin names its flag and where the answer is stored). `drive-mockup.py` clicks through
all scenarios headlessly with Playwright (`uv run python docs/plans/setup/drive-mockup.py
docs/design/10-setup-mockup.html`, Chrome channel).

The work starts now; refactor-2 is closed.

## Goal

`beamtime init` becomes an interactive, user-oriented setup (today it asks nothing). It may be the
first contact with Beamtime, so the experience must be excellent. The same command covers a first
setup, a teammate joining, a cluster login node, and updating an older setup.

## Principles (from the mockup)

- **Look first.** A local scan (no network, under a second) fills every default: git, the Python
  environment and its tool (uv, pip, conda), the framework (Lightning), SLURM scripts, past logs,
  notes, memory files, agents and their files, ssh hosts.
- **Yours to extend.** Detection only preselects. Every detected list takes the user's own entries
  ("+ Add a path", "+ Add a host"), checked the same way as found ones.
- **Many remotes.** Any number of hosts, checked together, then a path (and an install if missing) per
  host. Each becomes a source `@name`.
- **No trace before the review.** Nothing is written, installed or imported until the review is
  confirmed; ctrl-c leaves the project as it was.
- **One command.** Every answer is a flag; the wizard can print the whole setup as one
  `beamtime init --yes ...` command. Without a terminal it asks nothing and uses flags or defaults.
- **Two places.** Each answer says where it lands: `beamtime.yaml` (project, shared) or
  `~/.config/beamtime/settings.yaml` (this machine). A teammate gets only the machine's questions.
- **Judgment goes to agents.** Turning old notes and memory files into typed notes needs judgment; the
  wizard hands that to the chosen agent (an MCP `migrate` prompt) and can start it, but never calls a
  model itself. Setup without any agent ("None") is a first-class path.
- **Any terminal.** Arrow keys, space, Enter, numbers as shortcuts; standard library only (termios,
  msvcrt on Windows), numbered fallback. The CLI's import budget (`tests/test_budgets.py`) holds.
- **Voice.** Beamtime's: plain, short, no emoji, no exclamation marks.

## Decisions

1. **Settings levels for machine values.** Machine-specific values such as the cache may be set at
   both levels (user and project), with templates (`{user}`, `${VAR}`) so one value is valid for the
   whole team.
2. **Cache.** `cache` becomes a setting resolved by one function for every consumer (CLI, `serve`,
   MCP, `serve --stdio`), because an MCP server started by a harness doesn't inherit the shell's
   `BEAMTIME_CACHE`. nfs, Lustre and gpfs paths are refused; on a cluster the default is the index in
   memory, or a local-disk path such as `/tmp/{user}/beamtime-cache`.
3. **Log dir.** Asked on a first setup (default `beamtime/`); a path outside the project gets a link.
   On a cluster: link the log dir to scratch. `logdir` stays project-only.
4. **Remotes.** Hosts from `~/.ssh/config` and typed hosts; one probe for all; per host a path
   (variables expand on that host) and an optional `pip install --user` there after the review. The
   path goes to `beamtime.yaml`, host and command to the machine's settings. On 2FA clusters the
   wizard offers the ssh ControlMaster lines (shown in full, confirmed).
5. **Agents and MCP.** Any number of agents: Claude Code, Codex, Cursor, VS Code (Copilot), Gemini CLI,
   opencode, Windsurf, "Another agent" (prints its MCP config) and "None". The MCP command must work
   in **any environment** (uv, pip, conda, pipx, a global install), not an absolute path into a venv
   that can disappear; the spec decides how it is resolved per case.
6. **Agent behaviour.** Presets in `beamtime.yaml: agent`: Careful (today's behaviour, default),
   Hands-on (may launch runs), Analysis only (no proposals), or "Choose each setting". The knobs:
   - autonomy: `launch_runs` (never / ask / allowed), memory updates (suggest / after verdicts),
     save views (draft / save);
   - rigor: `research_record` (off / encouraged (default) / required), seeds per point (3),
     significance (0.95);
   - budgets: memory tokens (~1.5k), render rounds (2), custom blocks (built-in first / free);
   - conventions: main metric and direction, seed key (`config.seed`), domain (ml / simulation); the
     wizard does not detect or ask for them, the user sets them in `beamtime.yaml: agent` afterwards.
   Fixed, never settable: writes are additive; agents never run user-only commands; agents ask
   through the tools. `beamtime guide` reads the knobs and marks defaults as defaults.
7. **Agent rules: Beamtime is the record, or skip.** Exactly two choices. The block is written to each
   chosen agent's instruction file (CLAUDE.md for Claude Code, GEMINI.md for Gemini, AGENTS.md for the
   rest) between the `beamtime:start/end` markers, generated from the agent settings so text and
   settings agree. It says plainly that the experimental record lives in Beamtime: start a session with
   `memory_show` and `status`; answer questions about past experiments from Beamtime, not recollection
   or loose files; results, conclusions, dead ends and open questions go into notes, durable facts into
   memory — not into the instruction file, NOTES.md or the agent's own memory (which keeps coding
   preferences). The mockup's preview is the draft text. Skip writes no block (`--no-rules`); a later
   `beamtime init` offers it again. If the scan finds a conflicting instruction (e.g. "keep results in
   NOTES.md"), the wizard flags it and the agent hand-off folds that section into Beamtime, showing the
   diff before it edits the file.
8. **Past work.** Importers: TensorBoard, W&B offline, **MLflow**, CSV, and Beamtime log dirs. Runs are
   copied into `imported/<name>`; originals stay. Notes and memory files go to the agent (or come in
   as written without one). Claude Code's project memory is a detected source.
9. **Beamtime log dirs as past work.** Detected inside the project (runs outside the log dir), among
   the log dirs this machine's index cache already knows (other projects; offered, not ticked), and in
   typed paths. They copy with their proposals, notes and memory, with no conversion. Reading another
   project's runs in place (a local-path source) is out of scope.
10. **Import provenance.** An optional field in `_run.json` records the original path; old `_run.json`
    files keep loading. Write it into `docs/design/01-storage.md` before the code.
11. **Updating an older setup is `beamtime init` again**, not a separate migrate wizard. Data never
    migrates (every file reads in every later version); what goes stale is the setup around it: the
    rules block, the MCP command, skills, removed settings keys (e.g. `colormap`), the SDK in the
    project environment, Beamtime on remotes, and Beamtime runs outside the log dir. The wizard first
    checks and says the data is fine, then lists each stale item (before → after, all ticked), asks
    only questions new since that version, and ends with the few changes a person would notice.
    The setup's version is found by comparing the rules block with every release's text (no stamps).
    `beamtime status` prints one line when a project's setup is older; `beamtime init --check` lists
    what is stale without asking and exits non-zero (CI, agents).
12. **Extras.** Commit the research record (proposals, notes, memory, views) to git and ignore run data
    (`--git record|none`); add the SDK to the project environment with the project's own tool
    (`--sdk`); the wizard offers to start the chosen agent with the migrate prompt at the end.
13. **Multi-select behaviour.** The cursor starts on the first ticked row; Enter confirms the ticked
    set; after the user moves to an unticked row, Enter ticks it too and confirms ("this one too").
    The footer shows how many are selected.

## Decisions after the spec (2026-11-15)

Taken while W14, W15 and D11 were still queued; the spec and the plan follow them.

14. **Reconfigure after setup.** `beamtime setup` in a terminal, in a project that is set up and
    current, no longer says so in one line and asks nothing. It opens the existing "Change an answer"
    screen starting from the saved settings: every step with its current answer, then only what the
    user picks, then the usual review and apply. A rules block of this release whose
    `beamtime.yaml: agent` settings changed since is refreshed through this flow, not by `--check`
    (as the W13 review recommended).
15. **`beamtime init` becomes `beamtime setup`**, with no `init` alias, before 0.3 ships: the CLI, the
    operation (`SetupParams`), the generated CLI reference, the guide, the messages that print the
    command (the `status` line, the printed review command, errors) and the spec. The SDK's
    `beamtime.init()` keeps its name. Earlier decisions above say `init`; read them as `setup`.
16. **A proposal word limit.** `beamtime.yaml: agent.proposal_words` (default 150, in every preset),
    next to the other agent knobs (the project setting is `agent:`, singular). The wizard's agent
    settings form asks for it; `beamtime guide` names it in the agent instructions, marked as a
    default like the other knobs; `proposal set` gives a soft warning beyond it and never refuses,
    since proposals are frozen once a run records them.
17. **Out of scope here:** `beamtime ps`/`stop` and reusing a running `serve`; they are planned
    separately.

For the user docs (from the W13 review): `beamtime setup --yes` copies Beamtime runs found outside
the log dir into it by default (a copy, the originals stay; `--import ''` declines).

## Flags (as drafted in the mockup)

`--runs here|remote|both`, `--logdir`, `--remote <host>:<path>` (repeatable), `--install-remote`,
`--skip-remote`, `--ssh-share`, `--agents a,b | --no-agents`, `--agent-style`, `--agent-set k=v,...`,
`--no-rules`, `--import`, `--import-notes`, `--import-memory` (repeatable), `--git`, `--sdk | --no-sdk`,
`--role record|full`, `--link-logdir`, `--cache memory|<path>`, `--update <items>`, `--check`,
`--migrate-with <agent>`, `--yes`.

## Where to read first

`src/beamtime/ops/admin.py` (today's `init`, `mcp install`, the rules block), `src/beamtime/settings.py`,
`src/beamtime/index/cache.py` (`cache_dir`), `src/beamtime/guide/parts/instructions.md`,
`src/beamtime/mcp/server.py` (prompts), `docs/design/01-storage.md`, `docs/design/08-cli-mcp.md`,
`docs/guides/settings.md`, `docs/guides/remotes.md`, `docs/quickstart.md`.
