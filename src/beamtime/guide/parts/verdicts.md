# Verdicts

A verdict is a note of type `verdict`: a person's or agent's judgement of one proposal version. The
check computes; the verdict decides, and may disagree with the check if it says why.

## Write one

```
note_add group=scaling/warmup type=verdict proposal=<version> overall=confirmed
  description="Warmup removes the spike above lr 1e-4; samples not visibly sharper."
  verdict={no-spike: confirmed, warmup-helps: confirmed, sharper-samples: refuted}
  evidence=[<run id>, "scaling/warmup#warmup-helps"]
```

- `verdict` maps every prediction to `confirmed`, `refuted` or `inconclusive`; `overall` is the same
  three values. The check at the time of writing is added automatically, so the verdict stays
  traceable when more runs arrive.
- Manual predictions are decided only here: they count as the verdict says.
- The newest verdict on the current proposal version is the group's verdict. A new proposal version
  needs a new verdict.

## State what the check says and no more

- `insufficient`, `inconclusive`, `pending` and provisional results are said as such in the
  description: "provisional, 6 of 15 runs" is a fine verdict body; "confirmed" is not.
- Disagreeing with the check is allowed: `refuted` over a `pass` needs the reason in the body and
  evidence for it.
- Do not strengthen the claim in the description beyond the predictions: a prediction about
  `val/acc.max` does not confirm that the model "generalizes".
- Name what was not tested. A verdict is a statement about this proposal, not about the field.

## After a verdict

Update the group's memory (`guide memory`). A decision note records what happens next.
