# A nightly export, and the record it produces

The point of this example is the last line of [`transcript.md`](transcript.md):
Qedro prints its tombstone, meaning every activity in the record stands on emitted
evidence rather than on somebody's spreadsheet. The only change that made that
possible is the `declare(...)` wrapped around work `export.py` was already doing.

The script is the shape this package exists for — one table in, one file out, run by
cron, known to no orchestrator, so no OpenLineage integration can emit for it.

## Run it

```bash
pip install art30-emit qedro
cd examples/nightly-export

ART30_EMIT_FILE=events.jsonl python export.py
qedro ropa . --config qedro.yaml
```

Nothing needs to be running: `ART30_EMIT_FILE` appends the events to a file and Qedro
reads a directory of them. Against a real backend the only difference is
`OPENLINEAGE_URL` on one side and the Marquez URL on the other.

`transcript.md` is what those two commands printed, captured by
`tools/capture_example.py --check` rather than written by hand, so it fails CI when it
stops being true.

## Which Art. 30(1) item comes from where

| Item | Where it comes from | Evidence? |
|---|---|---|
| (a) controller | `qedro.yaml` | An organisation, not a pipeline |
| (b) purposes | the `processing` facet, from `declare(purpose=…)` | Emitted |
| (c) categories of subjects and of data | the `tags` facet, from `classify=…` | Emitted |
| (e) transfers to third countries | the `residency` tag | Emitted |
| (f) time limits for erasure | the `retention` tag | Emitted |
| (d) categories of recipients | `qedro.yaml`, marked `(declared)` | No lineage carries one |
| (g) security measures | `qedro.yaml`, marked `(declared)` | An arrangement, not an event |

The last two rows are the honest limit of this approach, and the record says so in
its own output rather than leaving a reader to work it out.

## What a second run looks like

`runs 1 in window` becomes `runs 2 in window` and the window widens. Run it with the
export's input file removed and the context manager emits `FAIL` with the
`FileNotFoundError` instead of `COMPLETE`, the exception still propagates, and the
record then has a job whose last run did not finish.
