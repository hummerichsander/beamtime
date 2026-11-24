# Remote machines

Your laptop's Beamtime shows a cluster's runs live over ssh; on the cluster only a short-lived
process runs.

`beamtime setup` does steps 1 to 3 (`--remote`, `--install-remote`, `--ssh-share`;
[Setting up a project](setup.md)). By hand:

## 1. Install Beamtime there

```sh
ssh mycluster 'pip install --user beamtime && ~/.local/bin/beamtime --version'
```

The remote needs Python 3.11+; keep both sides at the same version.

## 2. Log in without prompts

A key login works as is. With a second factor, share one login and log in once per session with
`ssh -fN mycluster`. In `~/.ssh/config`:

```
Host mycluster
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h-%p
  ControlPersist 12h
```

## 3. Name the remote

```sh
beamtime source add cluster mycluster:/scratch/myproject/beamtime
```

This finds how to start Beamtime there (a venv such as `.venv` in or above the log dir, the `PATH`,
`~/.local/bin`, venvs in your home or scratch, conda environments; `--command` says it yourself) and
writes the entry to your user settings (`--project`: to `beamtime.yaml`):

```yaml
remotes:
  cluster:
    host: mycluster                       # an ssh host or alias
    command: ~/.local/bin/beamtime        # how the remote shell runs Beamtime
    path: ${SCRATCH}/myproject/beamtime   # the log dir there; ~ and ${VAR} expand there
```

A teammate runs `beamtime setup` once to say how they reach the project's remotes;
`--skip-remote NAME` switches one off on this machine ([Settings](settings.md#remote-machines)).

## 4. Use it

```sh
beamtime doctor            # checks the login, Beamtime there and the log dir
beamtime serve --open      # the sidebar gets an @cluster section
beamtime runs @cluster     # from the command line
```

- Remote groups are `@cluster/...` everywhere, for reads and writes; lists merge both machines.
- View drafts stay local; validating and saving reach the cluster.
- Without a local project, `beamtime serve mycluster:/scratch/beamtime` works from an empty directory.
- A second `beamtime serve` for the same root prints the running one's URL
  ([Running processes](settings.md#running-processes)).

## When the cluster is away

```sh
beamtime pull cluster:scaling/lr-sweep
```

keeps a read-only copy of a group locally; when the cluster can't be reached, pages show it, marked
with its date.
