# Runs on a cluster

Inside a job Beamtime needs no server, network or database.

## Setting up the checkout

On a login node, `beamtime setup` asks only the machine's role (`record`, or also look at runs), where
runs go and whether to keep an index; a `beamtime.yaml` from git stays as it is. Without a terminal:

```sh
beamtime setup --yes --role record --link-logdir '${SCRATCH}/myproject/beamtime' --cache memory
```

## Where runs go

Put runs on scratch, not in your home directory. `--link-logdir` makes the log dir a link to scratch,
local to this checkout and kept out of git (a log dir holding runs is never replaced). In a job
script, the environment works too:

```sh
export BEAMTIME_LOGDIR=$SCRATCH/myproject/beamtime
```

## The index cache

On a network filesystem the index lives in memory ([Settings](settings.md#cache)). To keep one
between connections, put it on local disk:

```sh
beamtime setup --yes --cache /tmp/{user}/beamtime-cache
```

## Several GPUs or nodes

Only rank 0 records; other ranks get a no-op run, so the same script works with `torchrun`, SLURM
tasks and Lightning. Every rank's output is kept.

## SLURM

The run records the job id, array task and node. A job stopped at its time limit or preempted ends
as *killed*, with a note that a requeue was requested. To continue the same run after a requeue,
keep its id with your checkpoint:

```python
run = beamtime.init(dir="scaling/long-context", resume=checkpoint.get("run_id"))
checkpoint["run_id"] = run.id
```

The run then shows one curve across both jobs, with the restart marked.

## Seeing the runs

Copy them to your laptop (`rsync`) and run `beamtime serve` there, or read them live over ssh:
[Remote machines](remotes.md). A run that stops sending updates (a dead node) shows as *lost* after
five minutes.
