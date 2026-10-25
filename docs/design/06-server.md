# Layer 6: Self-hosted server

Status: **reviewed; post-v1.** The few hooks it needs are part of v1 (see
[What v1 must provide](#what-v1-must-provide)).

Besides running locally and querying remotes, Beamtime can run as a self-hosted server for a team,
like W&B but self-hosted and light: one process on a disk, because the files are the database.

## Two roles, one server

| Role | What it does | Source of truth | Needed for |
|---|---|---|---|
| **Hub** | a permanently running `serve` on a team machine that federates remotes (clusters, workstations) and serves the web UI, CLI and MCP to the team | the remotes, as in [layer 4](04-remotes.md) | teams sharing results that live on clusters |
| **Storage** | runs send their files to the server, which keeps them in its own log dir | the server | jobs without a shared filesystem with any Beamtime instance: cloud, Kubernetes, several clusters |

Both roles are the same `beamtime serve`, extended by users, several projects and an upload path. A
server can play both at once: some projects stored on it, others federated from clusters.

## Prior art

| Tool | Server | Weight |
|---|---|---|
| W&B Server | Kubernetes, MySQL, Redis, object storage | heavy |
| MLflow tracking server | one process, a SQL database, an artifact store | light, widely self-hosted |
| Aim remote tracking | a gRPC server in front of Aim's storage | light |
| Beamtime | one process, files on disk, the index as a cache | lighter still; backup is copying a folder |

## Architecture

- **One process** serves the web UI, the API (HTTP), MCP (HTTP transport) and the upload endpoint.
- **Projects** are roots on the server's disk, each a log dir with its own index cache, plus
  federated remotes configured per project.
- **Files stay the source of truth** for stored projects; the index is rebuilt from them as anywhere.
- **Writes by many users keep the one-writer rule**: notes, views and blocks are new files, written
  by the server on behalf of a user; run streams have exactly one writer, the uploading run.

## Users and permissions

- **Accounts with API tokens** first; single sign-on (OIDC) later.
- **Permissions per project**: read, write (notes, views, blocks, proposals), admin.
- **Every write carries an identity.** Authored files record `user` and `author`
  ([research record](09-research-record.md#fields)); on the server, `user` comes from the token.
- **Agents connect over MCP via HTTP** with a user's token and act with that user's permissions.

## Upload path (storage role)

The SDK keeps writing local files, exactly as in [layer 2](02-sdk.md). A separate **uploader** tails
them and sends what is new, so a run never depends on the network and finishes completely when the
server is unreachable; the upload catches up later.

The file rules of [layer 1](01-storage.md#write-protocol) make the upload protocol small and
idempotent:

| Operation | For | Rule |
|---|---|---|
| `append(path, offset, bytes)` | `_metrics.jsonl`, `_output.log`, other streams | accepted only if the file on the server is exactly `offset` bytes long; a retry after a lost response is harmless, a gap is rejected |
| `rotate(path, to)` | `_output.tail.log` | mirrors the rotation of the tail segment ([layer 1](01-storage.md#write-protocol)) |
| `put(path, bytes)` | `_run.json`, `_run_card.json`, `_preview.json` | replaces the file atomically |
| `create(path, bytes)` | data files, notes, view versions | fails if the file exists |

Trailing partial lines are never sent, as readers never read them. The uploader runs as:

- `beamtime push --follow <folder>`: a separate process, e.g. on a login node that has outbound
  network access while compute nodes don't;
- a thread started by the SDK when `BEAMTIME_SERVER` is set, for jobs with network access.

## Hub and clusters

A hub federates remotes as the laptop does in [layer 4](04-remotes.md), with one difficulty:
clusters often require two-factor logins and forbid unattended ssh, so a hub cannot always dial in.
Two ways to connect:

- **Hub dials in** over ssh with a service account, where the site allows it.
- **Cluster dials out**: `beamtime serve --connect https://hub.lab.org` on the login node opens an
  outbound connection to the hub with a token and serves queries over it. Outbound HTTPS from login
  nodes is usually allowed, and no inbound access or stored credentials are needed. The process
  lives only while its session lasts, as in layer 4.

## Security

- Custom view blocks written by other users run in the reader's browser. The sandbox of
  [layer 5](05-views.md#sandbox) (no same-origin access, no network, data only through the bridge)
  is what makes that safe, and the server enforces it with strict content security policies on
  every page.
- Tokens are scoped to projects and revocable; uploads are limited in size per run and project.

## What v1 must provide

v1 ships without the server. Only the hooks that would be hard to add later are part of v1:

1. **No network code in the SDK.** Runs write only files; the uploader is a separate component that
   tails them ([layer 2](02-sdk.md)).
2. **An identity on every authored file.** Proposals, notes, views, blocks and memory carry `author`
   (a person or model id) and `user` (the account) from v1 on.
3. **The sandbox designed for untrusted views** from the start ([layer 5](05-views.md#sandbox)).

Everything else is added with the server: an auth context and a project on every API request, the
upload operations of the `files` method, and MCP over HTTP.

## Open questions

1. **Server-side storage layout.** One log dir per project on local disk, or object storage (S3) for
   large deployments?
2. **Folder-level permissions.** Are project-level permissions enough, or do teams need them per
   folder?
