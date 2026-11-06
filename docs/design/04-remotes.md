# Layer 4: Remotes

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

Runs often execute on a cluster while the researcher and their agents work on a laptop. This layer
defines how the laptop sees and annotates runs whose files live elsewhere.

## Principles

1. **The remote is the source of truth.** Run files, notes, proposals, views, blocks and memory of a
   remote group live on the remote and nowhere else. There is no second writable copy.
2. **Data flows one way.** Answers and pulled snapshots travel from the remote to the laptop. Writes
   to a remote group are executed by Beamtime on the remote, so nothing is ever synced back.
3. **Only what is asked for travels.** A query moves its answer (rows, about 1000 points per curve),
   not the run files. The size of the remote log dir doesn't matter.
4. **One server, two transports.** The same `beamtime serve` code runs locally and remotely and
   speaks one API, over HTTP for browsers and over stdio for ssh.

## Prior art

| Tool | Remote approach | Writes |
|---|---|---|
| TensorBoard | run it on the remote and forward the port; or read `gs://`/`s3://` directly | read-only |
| W&B, MLflow, Aim server | one central server holds the data; runs send to it | go to the server |
| VS Code Remote-SSH, Jupyter | a server process on the remote, local UI over ssh | on the remote |
| raw log copies (rsync) | offline and archive use | two copies, conflicts |

Beamtime follows the common pattern: data stays where it is produced; questions and answers travel.

## Three modes

| Mode | What runs where | Use |
|---|---|---|
| **1. Remote query** | the laptop's `serve` starts `beamtime serve --stdio` on the remote over ssh and merges its answers with local runs | the default: the local UI and agents see local and remote runs together |
| **2. Port forwarding** | `beamtime serve` on the login node, its web UI reached through `ssh -L` | TensorBoard style: nothing needed on the laptop |
| **3. Pull** | `beamtime pull` copies a group to the laptop as a read-only snapshot | offline work, archives |

### Mode 1: remote query

```sh
beamtime serve                                   # local runs + all remotes from the settings
beamtime serve cluster                           # only this remote (plus local runs)
beamtime serve cluster:scaling                   # narrowed to a group of the remote's log dir
beamtime serve login.hpc.de:/scratch/me/beamtime # ad hoc, no settings needed
```

- **One connection per remote.** The local `serve` opens a long-lived ssh connection and runs
  `beamtime serve --stdio` there. No port is opened on the cluster, nothing passes a firewall, and
  with ssh `ControlMaster` a two-factor login is needed only once.
- **The remote indexes into a private temporary cache** by default (created at start, deleted on
  exit), lazily: each request catches up only the group it asks about, and no daemon walks the
  whole log dir. Most requests need little index data, since run tables come from run cards and
  overview charts from previews; zooms and exact statistics build column data, kept for the session.
  (SQLite in memory doesn't fit: every operation opens its own index.)
- **A persistent index** is used only where one is configured (`cache` below). Login nodes often have
  a small, purged `/tmp`, several nodes behind one host name, and home directories on NFS, where
  SQLite is unsafe; so nothing is written unless the user names a suitable disk. If two remote
  processes share a cache, the second falls back to memory.
- **Writes** (notes, proposals, view versions, blocks, memory) to a remote group are executed by the
  remote process under the usual rules. Without a connection the write fails with a clear message;
  nothing is queued.
- **Status is computed where the files are.** The remote judges heartbeats against its own clock. If
  the connection drops, the laptop shows the remote as "unreachable since 14:02" instead of guessing
  run states.
- **The remote process exits when its ssh connection closes.** With a configured `cache`, the next
  connection catches up on what changed; without one, it starts again from cards and previews.
- **One-shot CLI calls** go through the local `serve` when it runs, reusing its connections. Without
  it, each call opens its own ssh connection, which costs a few hundred milliseconds;
  `beamtime status` says so.

### Federation

The local `serve`, CLI and MCP send each query to every source in scope and combine the answers:

- **Listings are merged**: run rows, curves, logged data, timeline entries, groups. Run ids are unique
  across machines, so merging is concatenation. Sorting is applied after merging; for `limit`, each
  source returns its top `limit` rows by the same sort, so the merged top rows are exact.
- **Aggregates are computed per source**: group and seed means, `importance`, value ranges in `keys`,
  and prediction checks. A proposal belongs to a group and a group to one source, so checks never
  span sources. A query over several sources returns aggregates per source, labelled.

### Mode 2: port forwarding

```sh
ssh -L 8080:localhost:8080 cluster
beamtime serve --port 8080                       # on the login node
```

- This is the same `serve` as everywhere; its web UI runs on the login node.
- **A token is required.** Other users on a shared login node can reach its `localhost` ports, so
  `serve` generates a random token and prints the URL with it, as Jupyter does. Static library files
  (the bundled JavaScript) are public and served without the token, so sandboxed custom blocks can
  load them ([layer 7](07-web-ui.md#security)).
- Agents on the laptop can use the remote without a local Beamtime by registering
  `ssh cluster beamtime mcp` as their MCP server command.

### Mode 3: pull

```sh
beamtime pull cluster:scaling/lr-sweep
```

- Copies **every file of the group** and below, plus the `view/`, `blocks/` and `memory/` groups of
  its ancestors, so memory and library blocks keep working. Large data stays behind:
  `_data/` files above a size limit, `artifacts/` and `checkpoints/`.
- Copies incrementally: appended files transfer only their new bytes.
- Snapshots are **read-only** and live in the cache (`~/.cache/beamtime/<logdir-hash>/pulled/`), never in
  the user's log dir. They answer for their remote while it isn't connected, marked with the
  snapshot's time; run status is judged relative to that time.
- `beamtime pull` again refreshes; `beamtime pull --drop` removes the snapshot. Writing to a pulled
  group is refused.
- The transfer uses the same API (`files`: list, and read from an offset), so it needs no rsync.

### Routing and merging

- **A path names its source.** `@cluster/scaling` is the group `scaling` of the remote `cluster`, in
  parameters, answers, links and the web UI; local paths have no prefix.
- **Every operation whose target names a source** (`group`, `from`, `run`, a view or a query's
  `from`) runs on that source with the prefix stripped; paths in its answer get the prefix back.
  Operations on `.` that list (`groups`, `runs`, `series`, `data`, `timeline`, `notes`, `keys`) ask
  every source at once and merge; everything else stays local. Which operations list, write or
  work on drafts is a flag on each operation in the registry. A source that doesn't answer a listing
  within 20 s is left out of it (its snapshot answers if there is one) and marked in `meta.sources`.
- **Merging by answer kind**: run rows are sorted again with the query's sort and cut to its limit,
  exact because each source returned its top rows by that sort; groups, curves and data entries are
  concatenated in source order; timeline entries are merged by time and notes by id; `keys` unions
  names and adds run counts. Aggregated curves (`by`, `seeds`) are computed per source and labelled
  with it. The size cut for agents applies after merging.
- **Writes carry the laptop's author**: the laptop resolves `author` and passes it on; `user` is
  the account the remote process runs as.
- **One-shot CLI and MCP calls** that name a remote go through the local `serve` when it runs
  (localhost with its token), else open their own connection. Calls without a remote stay in-process.

## Naming remote groups

Every source is mounted under its own prefix in queries, the UI and links:

```yaml
from: .                     # everything: local and all connected remotes
from: scaling/lr-sweep      # local
from: "@cluster/scaling"    # the remote "cluster"
```

Sources are separate trees, even if their folder names match: a group that exists locally and on the
cluster is two groups, each with its own proposal, notes and view. Inheritance of views and blocks
stays within a source. Run ids are unique across sources, so links like `[[20261024-101532-k3m9xq2a]]`
work wherever the run is. In URLs, the local source is called `local` (`/f/local/scaling`).

**A source is a named log dir; `local` is one only when this machine has runs, otherwise it doesn't
exist** (`Context.has_local`): the log dir must exist, and either no remotes are configured or it
already holds a run — re-checked on every poll while remotes are configured, so a first local run
made after `serve` started is picked up without a restart. `serve` refuses only with no source at
all; without a local log dir it still writes `serve.lock`/`serve.json` (so `via_serve` finds the
port), and its indexing loop waits until a first local run creates the log dir. `@local/...` is accepted and stripped to a bare path, so an agent
that always writes `@name/group` doesn't need a special case. A path without a prefix means local
when it exists; with no local and exactly one remote, it means that remote (`Context.default_source`);
with several and no local, it is ambiguous and needs the prefix. Remotes here are the running
serve's (as named on its command line), else the configured ones. Listings of `.` still ask every
source, so the UI's tree names each root and its state. `/` and a bookmarked `/f/local`
redirect to the first source when there is no local one.

## Configuration

```yaml
# user settings, ~/.config/beamtime/settings.yaml
remotes:
  cluster:
    host: cluster                                  # an ssh host alias from ~/.ssh/config
    command: ~/venvs/bt/bin/beamtime               # how to start Beamtime there
    cache: /local/scratch/{user}/beamtime-cache    # optional persistent index; default: in memory
```
```yaml
# project settings, beamtime.yaml
remotes:
  cluster:
    path: ${SCRATCH}/proj/beamtime                 # the remote log dir
```

- **Two levels**, merged key by key ([layer 1](01-storage.md#settings)): a remote's `host`, `command`
  and `cache` usually live in the user settings, its `path` in the project.
- **Placeholders** keep `beamtime.yaml` shareable: `{user}` is the ssh user, and `${VAR}` expands an
  environment variable on the remote.
- **`cache` must be on a local disk.** On NFS, Lustre or GPFS the remote falls back to memory, and
  `beamtime status` says why. With several login nodes behind one host name, pointing `host` at one
  fixed node keeps the cache warm.
- **The command line overrides the settings** for one session: `beamtime serve cluster:scaling`,
  `--cache <dir>`, or an ad-hoc `host:/abs/path`. A name that matches a configured remote means that
  remote; anything else is an ssh host.
- Beamtime stores no credentials; authentication is the user's ssh configuration.
- `beamtime source add <name> <host:/path> [--command] [--cache] [--project]` writes the user
  settings by default (`--project` writes `beamtime.yaml` instead), probing ssh for the command
  (`command -v beamtime`, then the venv next to the path) unless `--command` is given.
  `source list` and `source rm <name>` read and edit the same settings; all three are user-only.

## Protocol

One API, two transports:

- **stdio** for ssh: newline-delimited JSON requests and responses, each with an id, so several
  requests can be in flight on one connection.
- **HTTP** for browsers and forwarded servers: `POST /api/<method>` with the same JSON.

The API's methods are **the operations of [layer 8](08-cli-mcp.md#operations)**, one method per
operation: every read (`keys`, `runs`, `series`, `card`, `notes`, `memory_show`, `check`, …), every
write (`note_add`, `proposal_set`, `memory_update`, `view_save`, `block_save`, …) and every view tool
(`view_validate`, `view_render`, …). CLI, MCP and the web UI are frontends of this one operation set.
Three methods exist only in the API:

| Method | Purpose |
|---|---|
| `hello` | version handshake; refuses incompatible major versions with both versions and the upgrade command |
| `subscribe` | notifications when runs or groups change, for live views ([layer 7](07-web-ui.md#live-updates)) |
| `files` | list files, and read a file from a byte offset, for `pull` |
| `view_check`, `view_put`, `view_compile` | validate, save or compile a bundled draft (`{group, yaml, files, blocks}`) against this machine's own group; views on a remote ([layer 5](05-views.md#agent-loop)) |
| `view_files` | read one of a page's view data or code files, for starting a draft from it |

Compatibility: the same protocol major version on both sides; minor versions only add. `hello`
carries the version, so a call to a method an older remote doesn't have (one of the four above, on
a remote built before they existed) answers with that version and the upgrade command, e.g. "`@au002a`
runs beamtime 0.1.1; this needs a newer version for view check: `uv pip install -U beamtime` there".

### Drafts on a remote {#drafts-on-a-remote}

A view or block draft always lives on the agent's own machine, never on the remote, even when it is
for a remote group: **the draft stays with the agent; the check and the write happen on the
source.** `view_new`/`block_promote` fetch the group's current view and files through the normal,
routed `view_show` and `view_files`; `view_validate`/`view_save` (and the promote the same way) pack
the draft's YAML and referenced files into one bundle, sent over the existing connection to
`view_check`/`view_put`, which materialize it in a temporary directory on the remote and run the
same static validation and `write_version` used for a local draft — so the check, the library and
the write path are identical, only the files travel. The source resolves the bundle's group in its own
index (a group or run below its log dir, nothing else), refuses `file` and `code` references that
leave the bundle, and refuses bundles over 16 MB; the sender checks the size before sending too. Rendering stays local and needs no change to
the remote: the renderer's own ephemeral `serve` answers the browser's `view` and `code` calls for
the draft itself (the files are already here), calling `view_compile` on the remote only to get the
compiled tree, so pins and library blocks resolve against the remote's own files; every other query
in that tree routes to the remote as usual.

## Testing

The client and federation are tested against a second log dir served over a plain command (no
ssh); the transport over real ssh against a Docker container with sshd and Beamtime installed. A
real cluster with two-factor login (`ControlMaster`) and SLURM follows as a recipe that only swaps
the host.

## Risks

- **Login node policies.** Some clusters kill long-running processes on login nodes. The remote
  process lives only as long as its ssh connection and is mostly idle; where a site still objects,
  mode 3 is the fallback.
- **Remote startup.** Python started from a cluster filesystem can take a second or more; the local
  `serve` keeps connections open, so this is paid once per session.
- **Offline.** Without a connection, remote runs are invisible unless pulled.

## Decisions

- The remote is the source of truth; data flows one way; writes to remote groups run on the remote.
- Three modes on one server and one API: remote query over ssh stdio, port forwarding with a token,
  and read-only pulls of whole folders.
- Listings are federated across sources; aggregates are computed per source.
- Each source is its own tree under a prefix (`@cluster/...`).
- The remote process exits when its ssh connection closes; its index lives in a temporary cache
  deleted on exit unless a `cache` on a local disk is configured.
- Paths carry their source (`@cluster/...`); operations route by their target, listings on `.`
  merge across sources.
- The API's methods are the operations of layer 8, plus `hello`, `subscribe`, `files` and the view
  bundle methods `view_check`, `view_put`, `view_compile` and `view_files`.
- Remotes are configured in user and project settings, with placeholders; no credentials are stored;
  `source add`/`list`/`rm` write and read that configuration.
- A source is a named log dir; `local` is one only when this machine has runs or no remotes are
  configured, checked fresh each time. View and block drafts always stay on the agent's machine;
  validating and saving one for a remote group send a bundle and run there.
