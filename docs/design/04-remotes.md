# Layer 4: Remotes

Status: **draft, under discussion**

Runs often execute on a cluster while the researcher and their agents work on a laptop. This layer
defines how the laptop sees and annotates runs whose files live elsewhere.

## Principles

1. **The remote is the source of truth.** Run files, notes, proposals and views of a remote folder
   live on the remote and nowhere else. There is no second writable copy.
2. **Data flows one way.** Answers and pulled snapshots travel from the remote to the laptop. Writes
   to a remote folder are executed by Beamtime on the remote, so nothing is ever synced back.
3. **Only what is asked for travels.** A query moves its answer (rows, ~1000 points per curve), not
   the run files. The size of the remote log dir doesn't matter.
4. **One server, two transports.** The same `beamtime serve` code runs locally and remotely. It
   speaks one API, over HTTP for browsers and over stdio for ssh. That makes the three modes below
   compatible without extra work.

## Prior art

| Tool | Remote approach | Writes |
|---|---|---|
| TensorBoard | run it on the remote, forward the port (`ssh -L`); or read `gs://`/`s3://` directly | read-only |
| W&B, MLflow, Aim server | one central server holds the data; runs send to it | go to the server |
| VS Code Remote-SSH, Jupyter | a server process on the remote, local UI over ssh | on the remote |
| raw log copies (rsync) | rare; offline and archive use | two copies, conflicts |

Beamtime follows the common pattern: data stays where it is produced, questions and answers travel.

## Three modes

| Mode | What runs where | Use |
|---|---|---|
| **1. Remote query** | `beamtime serve` on the laptop starts `beamtime serve --stdio` on the remote over ssh and merges its answers with local runs | the default: local UI and agents see local and remote runs together |
| **2. Port forwarding** | `beamtime serve` on the login node, its web UI reached through `ssh -L` | TensorBoard style: nothing installed or running on the laptop |
| **3. Pull** | `beamtime pull` copies selected groups to the laptop as a read-only snapshot | offline work, archives |

### Mode 1: remote query

```sh
beamtime serve                                   # local runs + all remotes from beamtime.yaml
beamtime serve cluster                           # only this remote (plus local runs)
beamtime serve cluster:scaling                   # narrowed to a group of the remote's log dir
beamtime serve login.hpc.de:/scratch/me/beamtime # ad hoc, no config needed
```

- The local `serve` opens one long-lived ssh connection per remote and runs `beamtime serve --stdio`
  there. Requests and answers are newline-delimited JSON on that connection. No port is opened on
  the cluster, nothing passes a firewall, and with ssh `ControlMaster` a 2FA login is needed only
  once.
- The remote process indexes its own log dir (layer 3) **in memory** by default, lazily: a folder
  is indexed when it is first queried, so connecting to a large log dir does not trigger a full
  rebuild. Running runs are then polled as in the local daemon. Most requests need no index at all:
  run tables come from run cards and overview charts from the runs' previews
  ([layer 1](01-storage.md#_previewjson)); only zooms and exact statistics build index data, parsed
  from `_metrics.jsonl` on first use and kept for the session.
- **A persistent index** is used only where one is configured (`cache` below). Login nodes often
  have a small, shared, regularly purged `/tmp`, several nodes behind one host name, and home
  directories on NFS, where SQLite is unsafe. So nothing is written unless the user names a
  suitable disk.
- **Federation.** The local `serve`, CLI and MCP send each query to every source (local log dirs and
  connected remotes) and merge the answers. Run ids are unique across machines, so merging rows and
  curves is a concatenation; sorting and limits are applied after merging.
- **Writes** (notes, views, proposals) to a remote folder are sent to the remote process, which
  writes the file there with the usual rules (new files, freezing, one writer). If the remote is not
  connected, the write fails with a clear message; nothing is queued.
- **Status is computed where the files are.** The remote judges heartbeats against its own clock, so
  a slow network never turns healthy runs into `lost`. If the connection drops, the laptop shows the
  remote as "unreachable since 14:02" instead of guessing run states.
- **The remote process exits as soon as its ssh connection closes.** It keeps nothing running on the
  login node between sessions. With a configured `cache`, the next connection only catches up on
  what changed; without one, it starts from the run cards and previews again.
- **One-shot CLI calls** go through the local `serve` when it runs, reusing its open connections.
  Without it, each call opens its own ssh connection and remote process, which costs a few hundred
  milliseconds; `beamtime status` points this out.

### Mode 2: port forwarding

```sh
ssh -L 8080:localhost:8080 cluster
beamtime serve --port 8080                       # on the login node
```

- This is the same `serve` as everywhere; its web UI simply runs on the login node.
- **A token is required.** Other users on a shared login node can reach its `localhost` ports, so
  `serve` generates a random token and prints the URL with it, as Jupyter does. Requests without the
  token are refused.
- Agents on the laptop can use the same remote without a local Beamtime by registering
  `ssh cluster beamtime mcp` as their MCP server command; MCP's stdio transport works over ssh as
  is.
- A local `serve` can also use a forwarded server as a source (`http://localhost:8080` plus token)
  instead of starting its own ssh process. That is how modes 1 and 2 combine: both talk to the same
  API.

### Mode 3: pull

```sh
beamtime pull cluster:scaling/lr-sweep
```

- Copies the group's run files, notes, proposals and views into a local snapshot, incrementally:
  appended files transfer only their new bytes. Checkpoints and other large artifacts stay
  references, as everywhere.
- Snapshots are **read-only** and live in the cache (`~/.cache/beamtime/<root-hash>/pulled/`), not in
  the user's log dir, so they never mix with local runs. They appear in queries as their remote,
  marked with the time of the snapshot.
- A snapshot can be refreshed by pulling again and removed with `beamtime pull --drop`. Writing to a
  pulled folder is refused; writes need the remote.
- The transfer uses the same stdio protocol (list files, read from an offset), so pulling needs no
  rsync, which differs between platforms (macOS ships `openrsync`).

## Naming remote folders

Every source is mounted under its own prefix in queries, the UI and links:

```yaml
from: .                     # everything: local and all remotes
from: scaling/lr-sweep      # local
from: "@cluster/scaling"    # the remote "cluster"
```

Sources are separate trees, even if their folder names match. A folder that exists both locally and
on the cluster is two folders, each with its own proposal, notes and view. The prefix makes clear
where data lives and where a write will go, and no file ever has to be reconciled between sources.
Inheritance of views stays within a source: a remote folder inherits views from its remote
ancestors. Links between notes use run ids,
which are unique across sources, so `[[20261024-101532-k3m9xq2a]]` works whatever side the run is on.

## Configuration

```yaml
# beamtime.yaml: the only configuration file
remotes:
  cluster:
    host: cluster                        # an ssh host alias from ~/.ssh/config
    path: /scratch/{user}/proj/beamtime  # the remote log dir; {user} is the ssh user
    command: beamtime                    # how to start Beamtime there, e.g. a venv path
    cache: /local/scratch/{user}/beamtime-cache   # optional persistent index; default: in memory
```

- **One file holds all configuration.** Whether it is committed is the user's choice. Placeholders
  keep it shareable: `{user}` is the ssh user, and `${VAR}` expands an environment variable on the
  remote (e.g. `${SCRATCH}/proj/beamtime`), so one entry fits everyone on the team.
- **`cache` must be on a local disk.** The remote checks it: on NFS, Lustre or GPFS it falls back to
  memory, and `beamtime status` says why. With several login nodes behind one host name, a
  node-local cache exists per node; pointing `host` at one fixed node keeps it warm.
- **The command line overrides the file** for one session. `beamtime serve cluster:scaling`
  narrows the configured remote to a group, `--cache <dir>` sets the persistent index, and
  `beamtime serve host:/abs/path` defines an ad-hoc remote. A name that matches a configured remote
  means that remote; anything else is an ssh host.
- Beamtime stores no credentials. Authentication is entirely the user's ssh configuration.

## Protocol

One API, two transports:

- **stdio** for ssh: newline-delimited JSON requests and responses, each with an id, so several
  requests can be in flight on one connection.
- **HTTP** for browsers and forwarded servers: `POST /api/<method>` with the same JSON.

| Method | Purpose |
|---|---|
| `hello` | version handshake; refuses incompatible major versions with a clear message |
| `status` | indexer state, running runs, last change |
| `query` | any query of layer 3 in its object form |
| `write` | create a note, save a view version, set a proposal |
| `subscribe` | push notifications when runs or folders change, for live views |
| `files` | list files and read them from an offset, for `pull` |

The remote's Beamtime version must be compatible: same protocol major version, additive minor
changes only. A mismatch is reported at `hello` with both versions and the upgrade command.

## Consequences for earlier layers

- **Layer 3:** the parked question about sync and indexing is resolved. Each machine indexes its own
  files; status, including `lost`, is computed where the files are.
- **Layer 1:** no file is ever synced back, so the earlier "sync is a union of files" is gone. The
  one-writer rule stays essential, because agents on the cluster and writes sent from the laptop
  both create files there.

## Risks

- **Login node policies.** Some clusters kill long-running processes on login nodes. The remote
  process lives only as long as its ssh connection and is idle most of the time, but a site may
  still object; mode 3 is the fallback.
- **Remote startup.** Python started from a cluster filesystem can take a second or more. The local
  `serve` keeps connections open, so this is paid once per session.
- **Offline.** Without a connection, remote runs are invisible unless pulled. A small local cache of
  remote run cards for an offline overview is a possible later addition.

## Decisions

- The remote is the source of truth; data flows one way, and writes to remote folders are executed
  on the remote.
- Three modes on one server and one API: remote query over ssh stdio, port forwarding with a token,
  and read-only pulls.
- Each source is its own tree under a prefix (`@cluster/...`). A folder, its proposal, notes and view
  live in exactly one place; `from: .` covers all sources.
- The remote process exits when its ssh connection closes.
- The remote index lives in memory by default; a persistent `cache` on a local disk can be
  configured per remote. Run cards and previews make most requests independent of any index.
- All configuration lives in one `beamtime.yaml`, with `{user}` and `${VAR}` placeholders; the
  command line overrides it per session. No credentials are stored.
