# Scripts: Python over the operations

The operations compute the statistics, intervals and per-run summaries, and every reader of the record
shares the numbers they return. Python is for joining, filtering and formatting their answers, never for
arriving at the numbers: before computing one yourself, look for the operation or field that returns it
(`guide analysis`, `guide queries`).

## When to write Python

- Several answers must be joined, reshaped or filtered by a condition the query language has no word for.
- A table or a sentence must be formatted from many answers in one go.
- Not for a mean, an interval, a correlation, a best step or a verdict: `runs`, `series`, `compare`,
  `importance` and `check` already answer them. A verdict comes from `check` and nowhere else.

## The `script` tool

Send the code in `script`'s `code` (CLI: `beamtime script`, the code on stdin; `--timeout <seconds>`).
`bt` is preloaded: every operation that is not user-only is a function that takes the operation's
parameters as keyword arguments and returns its answer as a plain dict, whole and unpaged.

```python
answer = bt.runs(from_="scaling/lr-sweep", limit=50)
rows = [dict(zip(answer["columns"], row)) for row in answer["rows"]]
print(sum(r["run.status"] == "finished" for r in rows), "finished of", len(rows))
```

- `from` is a Python keyword: write `from_=` or pass a dict, `bt.runs({"from": "scaling/lr-sweep"})`.
- `bt.ops()` names the operations, `bt.params("runs")` describes one's parameters, and a wrong parameter
  name is answered with the names the operation takes.
- Only what you `print` comes back (stdout is cut at 20,000 characters, the end of stderr is kept). Print
  the result, not the answers: print a table or a few numbers.
- Reads are cached for five minutes in `.beamtime/bt-cache/`, so asking twice costs nothing; a write
  through `bt` drops the cache.
- The timeout is 60 seconds by default (at most 600). The code runs in the project root with your
  rights, and the same rules as for the tools apply: writes are additive and user-only commands are
  handed to the user.

## Without MCP

Write the same code as a plain script with `from beamtime import bt`, or pipe it to `beamtime script`.
