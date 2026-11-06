# Remote machines

Beamtime on your laptop can show a cluster's runs next to your own, live, over ssh. Nothing runs
on the cluster except a short-lived Beamtime process started by ssh.

## 1. Install Beamtime there

```sh
ssh mycluster 'pip install --user beamtime && ~/.local/bin/beamtime --version'
```

The remote needs Python 3.11 or newer. Keep both sides at the same version.

## 2. Log in without prompts

A key login works as is. With a second factor, let ssh share one login and log in once per session
with `ssh -fN mycluster`. In `~/.ssh/config`:

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

probes ssh for how to start Beamtime there and writes the entry to your user settings. To share it
with a team, pass `--project` instead, or edit `beamtime.yaml` by hand:

```yaml
remotes:
  cluster:
    host: mycluster                       # an ssh host or alias
    command: ~/.local/bin/beamtime        # how the remote shell runs Beamtime
    path: ${SCRATCH}/myproject/beamtime   # the log dir there; ~ and ${VAR} expand there
```

## 4. Use it

```sh
beamtime doctor            # checks the login, Beamtime there and the log dir
beamtime serve --open      # the sidebar gets an @cluster section
beamtime runs @cluster     # from the command line
```

Remote groups are named `@cluster/...` everywhere, reads and writes alike: notes, proposals,
memory, views and library blocks. A view draft still lives on your own machine; only
validating and saving it reach the cluster. Lists of runs, groups and notes merge both machines.
A laptop with no runs of its own works the same way: `beamtime serve mycluster:/scratch/beamtime`
from an empty directory needs no local project at all.

## When the cluster is away

```sh
beamtime pull cluster:scaling/lr-sweep
```

keeps a read-only copy of a group on your laptop. When the cluster can't be reached, pages show the
copy, marked with its date.
