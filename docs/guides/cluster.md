# Runs on a cluster

Beamtime runs inside your job like on your laptop: it needs no server, no network and no database
on the cluster.

## Setting up the checkout

On the cluster, in your project's checkout:

```sh
beamtime setup
```

On a login node it asks only the cluster questions: what the machine does (`record` only, or also
look at runs), where runs go, and whether to keep an index between connections. Without a terminal:

```sh
beamtime setup --yes --role record --link-logdir '${SCRATCH}/myproject/beamtime' --cache memory
```

If the project already has a `beamtime.yaml` from git, it is left as it is. The cluster questions
come again whenever you run `beamtime setup` there; with nothing to change it ends with "Nothing to
change." See [Setting up a project](setup.md).

## Where runs go

Put runs on scratch space, not in your home directory. `--link-logdir` makes the project's log dir a
link to scratch (the link is local to this checkout, so it is kept out of git, and a log dir that
already holds runs is never replaced). For a job script or a one-off, the environment variable
works too:

```sh
export BEAMTIME_LOGDIR=$SCRATCH/myproject/beamtime
```

## The index cache

Beamtime keeps its index cache in `~/.cache/beamtime/`. SQLite is unsafe on network filesystems, so
a cache on NFS, Lustre, GPFS, BeeGFS, CIFS or sshfs is refused: the index then lives in memory for
the length of the process, and `beamtime doctor` says why. To choose where it goes, set `cache` in
`~/.config/beamtime/settings.yaml` (see [Settings](settings.md#cache)), or give `--cache` to
`beamtime setup`:

```sh
beamtime setup --yes --cache /tmp/{user}/beamtime-cache   # local disk, kept between connections
beamtime setup --yes --cache memory                       # no index kept
```

`BEAMTIME_CACHE` overrides the setting for one session.

## Several GPUs or nodes

Only rank 0 records. Other ranks get a stand-in run that does nothing, so the same script works
with `torchrun`, SLURM tasks and Lightning without changes. What every rank prints is still kept,
per rank.

## SLURM

Beamtime records the job (id, array task, node) with the run. When SLURM stops a job at its time
limit or for preemption, the run ends as *killed*, with a note that a requeue was requested.

To continue the same run after a requeue, keep its id with your checkpoint and pass it back:

```python
run = beamtime.init(dir="scaling/long-context", resume=checkpoint.get("run_id"))
checkpoint["run_id"] = run.id
```

The run then shows one curve across both jobs, with the restart marked.

## Seeing the runs

Two ways to look at runs that live on the cluster:

- Copy them to your laptop now and then (`rsync`), and run `beamtime serve` there.
- Let your laptop's Beamtime read them over ssh, live: see [Remote machines](remotes.md).

A run that stops sending updates (the node died) shows as *lost* after five minutes.
