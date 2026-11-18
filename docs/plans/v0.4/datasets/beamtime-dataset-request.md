# A native dataset object

Feature request for `hummerichsander/beamtime`.

**Status: written, not yet filed.** The issue URL goes here once it exists. To file it:
`gh issue create --repo hummerichsander/beamtime --title "A native dataset object" --body-file docs/beamtime-dataset-request.md`.

beamtime 0.1.1 can log a run and its metrics, but it has no notion of the data a run produced or consumed. Datasets
therefore live outside it, in a shared directory with a card per dataset, and the link between a card and a beamtime
group is prose that nobody can check. This asks for a read-only `dataset` object that reads those cards. It does
not ask beamtime to own them.

## What is missing

The object model is root, groups, runs. `sdk/run.py` `init()` (line 903 in 0.1.1) records a run's config, tags and
metrics, and no inputs. A dataset is cross-project: `md-simulations` generates a trajectory, `split-flows-public`
derives a resampled file from it and trains on that, and a third project may read the same bytes. A log dir is
per-project, so no group is the natural home. The loop `md-sim run -> produced dataset -> consumed by a training
run` exists only as prose.

Evidence from writing 20 cards (and 14 archive stubs) over the data root:

- The card for a generated dataset names its beamtime group (`provenance.beamtime: {project, group}`), and I could
  not verify one. Agents are forbidden from running `beamtime` commands, so the only source for a group name is a
  line of prose in a `CLAUDE.md`. `cln-ms` carries `{project: md-simulations, group: cln/AMBER14_implicit_330K}`
  taken from such a line; nothing confirmed it exists.
- For the other nine cards that carry the field (`ala2-ms`, `hexadecane-ms`, `trp-cage-ms` and the six derived
  `ala3-ms`, `ala5-ms`, `ala8-ms`, `ala12-ms`, `ala16-ms`, `ala32-ms`) no config, summary or script records a
  group, so the value is `beamtime: unknown`. That is nine of ten.
- The six alanine cards are derived by `scripts/prepare_alanine_systems.py` from md-simulations runs that live
  outside the root (`derived_from: [md-simulations/data/alaX/ala5_AMBER14_implicit_330K]`, for `ala5-ms`); their
  `provenance.configs` is `unknown` as well, as it is for `hexadecane-ms` and `trp-cage-ms`. Nothing links the
  produced trajectory back to the run, or the run to a group.
- The card standard deliberately keeps experiment findings out of the cards (they belong to the group's memory in
  beamtime). That leaves a card as a dataset description with a dangling pointer to the group holding what was
  learned from it, and no tool resolves the pointer in either direction.

## What exists instead

A `datacard.yaml` per dataset in a shared root, `/remote/gpu04/hummerich/data`, reached from each project through a
gitignored `data/` symlink. The root is a git repository that tracks only the cards, `SCHEMA.md` and
`check-datacards.py`. `SCHEMA.md` is the spec and the validator enforces it. Excerpt of the card:

```yaml
name: cln-ms
kind: generated                 # generated | derived | external | archived
status: active
created: 2026-10-04
provenance:
  project: md-simulations
  configs: [configs/cln-amber14-implicit-330K-r00.yaml]
  beamtime: {project: md-simulations, group: cln/AMBER14_implicit_330K}
files:
  traj_amber14_hresampled.trr: {frames: 196000, spacing_ps: 20, added: 2026-10-04, contents: ...}
verification:
  - the constrained twin reproduces energies.csv to 1e-3 kJ/mol
consumers:
  - split-flows-public/config/cln-{prior,egnn}.yaml
```

Required blocks per kind: `generated` needs `system`, `provenance.beamtime`, `verification`; `derived` needs
`system`, `provenance.derivations`, `derived_from`; `external` needs `source.license` and `source.citation`;
`archived` needs `superseded_by` or `reason`. A fact no source states is the string `unknown`. The card file is
the source of truth and should stay so.

## What is proposed

A read-only `dataset` object, discovered from a configured data root (one setting; each immediate subdirectory,
and each subdirectory of `old/`, with a `datacard.yaml`):

- `beamtime dataset list`: name, kind, status, size, and whether `provenance.beamtime` resolves to a group.
- `beamtime dataset show <name>`: the card, with `provenance.beamtime` checked against the known groups and
  `derived_from` followed to the parent card.
- `consumed_by`: computed by matching run configs that name a dataset (by directory name or path under the
  root), instead of the hand-maintained `consumers:` list.

Reading is the whole job: cards are parsed with `pyyaml` (already a beamtime dependency), unknown keys are kept,
and a bad card is reported rather than fatal. `pull` (remote group to read-only snapshot) is the nearest existing
precedent for a cross-project read-only object.

The payoff for the evidence above: an unresolvable `group` shows up as a broken link in `dataset list`, and the
group's page can list the datasets it produced and consumed.

## What is not proposed

- Datasets as zero-metric runs in a `datasets/` group. `beamtime gc` removes ended runs that never logged a metric
  (`ops/admin.py`), so those datasets would be deleted.
- beamtime writing, validating or owning cards. The file in the data root stays the source of truth;
  `check-datacards.py` stays its validator.
- Any change to the `Run` SDK, including recording a run's inputs there.
- Moving or tracking dataset bytes.
