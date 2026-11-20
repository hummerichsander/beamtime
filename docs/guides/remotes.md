# Remote machines

Beamtime on your laptop can show a cluster's runs next to your own, live, over ssh. Nothing runs
on the cluster except a short-lived Beamtime process started by ssh.

`beamtime setup` does steps 1 to 3: it checks the hosts in `~/.ssh/config`, can install Beamtime and
add the ssh lines, and writes the remote ([flags](setup.md): `--remote`, `--install-remote`,
`--ssh-share`). By hand:

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

probes how to start Beamtime there and writes the entry to your user settings; `--project` writes it
to `beamtime.yaml` for the team:

```yaml
remotes:
  cluster:
    host: mycluster                       # an ssh host or alias
    command: ~/.local/bin/beamtime        # how the remote shell runs Beamtime
    path: ${SCRATCH}/myproject/beamtime   # the log dir there; ~ and ${VAR} expand there
```

A teammate runs `beamtime setup` once; it asks only how they reach the project's remotes.
`--skip-remote NAME` switches one off on this machine ([Settings](settings.md#remote-machines)).

## 4. Use it

```sh
beamtime doctor            # checks the login, Beamtime there and the log dir
beamtime serve --open      # the sidebar gets an @cluster section
beamtime runs @cluster     # from the command line
```

A second `beamtime serve` for a root that already has one prints the running one's URL. `beamtime ps`
lists the serves, `beamtime stop` ends one ([Running processes](settings.md#running-processes)).

Remote groups are `@cluster/...` everywhere, for reads and writes. View drafts stay local; validating
and saving reach the cluster. Lists merge both machines. Without a local project,
`beamtime serve mycluster:/scratch/beamtime` works from an empty directory.

## When the cluster is away

```sh
beamtime pull cluster:scaling/lr-sweep
```

keeps a read-only copy of a group on your laptop. When the cluster can't be reached, pages show the
copy, marked with its date.
