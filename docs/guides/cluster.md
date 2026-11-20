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

A `beamtime.yaml` from git is left as it is. See [Setting up a project](setup.md).

## Where runs go

Put runs on scratch space, not in your home directory. `--link-logdir` makes the log dir a link to
scratch (local to this checkout, kept out of git; a log dir that holds runs is never replaced). For
a job script, the environment variable works too:

```sh
export BEAMTIME_LOGDIR=$SCRATCH/myproject/beamtime
```

## The index cache

A cache on a network filesystem is refused and the index lives in memory, since SQLite is unsafe
there ([Settings](settings.md#cache)). To keep one on local disk, set `cache` or pass `--cache`:

```sh
beamtime setup --yes --cache /tmp/{user}/beamtime-cache   # local disk, kept between connections
beamtime setup --yes --cache memory                       # no index kept
```

## Several GPUs or nodes

Only rank 0 records; other ranks get a no-op run, so the same script works with `torchrun`, SLURM
tasks and Lightning. Every rank's output is kept, per rank.

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

- Copy them to your laptop now and then (`rsync`), and run `beamtime serve` there.
- Let your laptop's Beamtime read them over ssh, live: see [Remote machines](remotes.md).

A run that stops sending updates (the node died) shows as *lost* after five minutes.
