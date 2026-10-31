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

In your project's `beamtime.yaml`:

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

Remote groups are named `@cluster/...` everywhere. Notes and verdicts you add to them are written
on the cluster. Lists of runs, groups and notes merge both machines.

## When the cluster is away

```sh
beamtime pull cluster:scaling/lr-sweep
```

keeps a read-only copy of a group on your laptop. When the cluster can't be reached, pages show the
copy, marked with its date.
