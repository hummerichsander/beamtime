# Runs on a cluster

Beamtime runs inside your job like on your laptop: it needs no server, no network and no database
on the cluster.

## Where runs go

Put runs on scratch space, not in your home directory:

```sh
export BEAMTIME_LOGDIR=$SCRATCH/myproject/beamtime
```

Beamtime keeps its index cache in `~/.cache/beamtime/`. If your home directory is on a network
filesystem, point the cache at local disk: `export BEAMTIME_CACHE=/tmp/$USER/beamtime-cache`.

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
