# Contributing

## What this package is for, so a change can be judged against it

Two rules decide most questions here, and a change that breaks either needs an
argument rather than a review.

**It emits the published facet, not one of its own.** The `processing` schema is
generated in [`cordata-tech/qedro`](https://github.com/cordata-tech/qedro) from a
governance model, and the classification rides on the standard `TagsDatasetFacet`.
This is the second implementation of that schema rather than a second definition
of it. A private spelling of either would make the package a vocabulary wearing a
standard's clothes.

**It decides nothing.** No validation against a compiled list of purposes, no
legal basis inferred from a job name, no default filling a field nobody declared.
A field the caller did not set is **absent** on the wire, never empty — *nobody
said* and *we say it is none* are different answers to an auditor, and only the
first can be corrected later.

## Running it

```bash
uv venv && uv pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

The worked example needs `qedro` as well, and CI checks that its transcript still
matches what the commands print:

```bash
uv pip install qedro
python tools/capture_example.py --check
```

If it fails because the output genuinely changed, rerun without `--check` and
commit the result. The transcript is captured rather than written, so that a
claim on the front page cannot quietly stop being true.

## Releases

The version has one source, `art30_emit.__version__`, and `pyproject.toml` reads
it. Pushing a `v*` tag publishes to PyPI through trusted publishing; the workflow
fails if the tag disagrees with the version, or if `CHANGELOG.md` has no dated
entry for it. A tag is a release decision rather than a bookkeeping step.

`workflow_dispatch` on the release workflow is a dry run: everything except the
upload, which is how the workflow gets proved before a tag exists.

## Style

`ruff check` and `ruff format`, line length 100, Python 3.12 and up. Comments
explain *why* rather than *what*, and a comment saying why a simpler thing was
rejected is worth more than one restating the line below it.
