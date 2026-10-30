# Recipe: a remote over ssh

How to see a remote machine's runs next to this machine's, and to check that it works. The
Docker end-to-end test (`BEAMTIME_DOCKER=1 pytest tests/remote/test_docker.py`) does the same
against a container.

## 1. Beamtime on the remote

The remote needs Python 3.11+ and the base install (no `serve` extra). From a checkout:

```sh
uv build --wheel
scp dist/beamtime-*.whl <host>:
ssh <host> '~/.local/bin/uv tool install --force ./beamtime-*.whl && ~/.local/bin/beamtime --version'
```

Both sides need the same protocol version: reinstall after updating Beamtime here.

## 2. A login without prompts

The connection runs in the background with `BatchMode=yes`. A key login works as is. With a
second factor, let ssh share one login (in `~/.ssh/config`) and log in once per session with
`ssh -fN <host>`:

```
Host <host>
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h-%p
  ControlPersist 12h
```

## 3. The remote in the settings

In the project's `beamtime.yaml` (or `~/.config/beamtime/settings.yaml` for every project):

```yaml
remotes:
  cluster:
    host: <host>                     # an ssh host or alias
    command: ~/.local/bin/beamtime   # as the remote shell runs it
    path: ${SCRATCH}/proj/beamtime   # the remote log dir; ~, ${VAR} and {user} expand there
    cache: /local/{user}/bt-cache    # optional; never on NFS, Lustre or GPFS
```

## 4. Check

```sh
beamtime doctor                     # ssh login, Beamtime there, its log dir and cache
beamtime runs @cluster              # one call, its own connection
beamtime serve --open               # the tree gets an @cluster root; listings merge
beamtime note add @cluster/<group> --type observation --description "From the laptop."
ssh <host> 'ls <path>/<group>/notes'   # the note is on the remote
beamtime pull cluster:<group>       # a read-only snapshot for when the remote is away
```

## On a cluster with SLURM

Run a training script with `beamtime.init()` in a batch job (`examples/` has a toy script and a
SLURM job) and watch it from the laptop: the run appears under `@cluster/...`, its curves update
live, and `_run.json` records the job (`scheduler`).
