# AGENTS.md

Instructions for a coding agent, or a person, changing this repository. They are the
short form of [CONTRIBUTING.md](CONTRIBUTING.md), which gives the reasons; where the two
ever disagree, CONTRIBUTING.md is right and this file is the bug.

art30-emit puts the OpenLineage Art. 30 `processing` facet on the wire from code that
emits nothing today, through a context manager or a wrapper around any command. It is
the second implementation of a facet schema published in
[`cordata-tech/qedro`](https://github.com/cordata-tech/qedro), and it sends events and
reads nothing.

## How a change gets in

- **Fork, branch, open a pull request against `main`.** Do not push to `main`, and do not
  create, move or delete a `v*` tag: pushing one publishes to PyPI, where a version can
  never be reused. Releases are the maintainer's.
- **The checks have to pass**, the same ones CI runs on Python 3.12, 3.13 and 3.14:

  ```bash
  pip install -e ".[dev]"
  pytest -q
  ruff check . && ruff format --check . && codespell
  # or once: pre-commit install, to run ruff and codespell before each commit
  pip install qedro && python tools/capture_example.py --check
  ```

- **Add a test for the behaviour you change**, named for what it protects ("a field
  nobody declared is absent rather than empty"), not for the function it calls.
- **Add a line under `## Unreleased` in `CHANGELOG.md`**, saying what a user would notice.
- **Sign off every commit** with `git commit -s`. The `Signed-off-by:` line is your
  statement under the [Developer Certificate of Origin](https://developercertificate.org)
  that you may contribute the change under the Apache-2.0 licence; the DCO check fails a
  pull request where a commit lacks one matching its author. **Sign the commit** too, with
  an SSH or GPG key, and explain the reasoning in the message rather than the diff.
- **Agents are welcome, and saying so is welcome too, not required.** If one helped, a
  line in the pull request on what it did and what you checked yourself helps a reviewer
  know where to look; a trailer such as `Assisted-by: <tool>` is fine as well. Either way,
  the person opening the pull request is responsible for every line, has read every
  line, and answers review on it.
- **A pull request that touches a path listed separately in `.github/CODEOWNERS`** says in
  its description which commitment below it keeps.

## Ask before changing these

An agent asks the person it works for before modifying any of these, naming the path and
what the change would do on the wire — for example: *"This renames a field in the
`processing` facet, so qedro would stop reading it from events this package already
sent. Do you want that?"*

- `FACET_KEY` and `FACET_SCHEMA` in `src/art30_emit/__init__.py` — the strings qedro and
  pipeline-runtime match on.
- How a declaration becomes facets in `src/art30_emit/emit.py` — what every user's
  events carry.
- How the wrapper runs a command in `src/art30_emit/__main__.py` — it executes what it is
  given.
- `dependencies` in `pyproject.toml` — the base install is one package.
- `.github/workflows/` — `release.yml` publishes to PyPI.

## Never

- **Never define the facet here.** Its schema is generated in qedro from a governance
  model; a field is added there first, and this package follows. Classification rides on
  the standard `TagsDatasetFacet`, never a private spelling of it.
  `test_the_facet_carries_the_declared_fields_and_the_published_schema` and
  `test_classification_rides_on_the_standard_tags_facet` fail when either drifts.
- **Never decide on the caller's behalf.** No validation against a compiled list of
  purposes, no legal basis inferred from a job name, no default for a field nobody
  declared. A field the caller did not set is absent on the wire, never empty
  (`test_a_field_nobody_declared_is_absent_rather_than_empty`).
- **Never read anything or open a connection of its own.** Where events go is
  `openlineage-python`'s decision, through its own configuration or `ART30_EMIT_FILE`.
  No new transport, no credential, no HTTP client.
- **Never let the record change what happens.** An exception inside `declare` emits
  `FAIL` and propagates unchanged (`test_a_failure_emits_fail_and_still_raises`); the
  wrapper forwards the command's output and exit status untouched
  (`test_the_command_runs_and_its_output_is_untouched`,
  `test_a_non_zero_exit_emits_fail_and_is_forwarded`).
- **Never run a command through a shell.** `subprocess.run` with an argument list, so
  `;` or `$(…)` in an argument stays an argument.
- **Never edit the worked example's transcript by hand.**
  `examples/nightly-export/transcript.md` is captured by `tools/capture_example.py`, and
  CI fails when a fresh run disagrees with it.

## How to work here

- **Check a facet or field name against the source** before using it: the published
  schema in qedro's `schemas/openlineage-art30-processing-facet.json`, and the
  OpenLineage spec for standard facets. A plausible name that does not exist is the error
  that looks most like work.
- **A bug fix starts with a failing test**, and you check it fails without the fix.
- **Run the worked example**, not only the tests: it pushes events from this package
  through qedro from PyPI, which is the claim the README makes.
- **One concern per pull request.** No reformatting, renaming or tidying along the way.
- **No new runtime dependency without an issue first.**
- **Security problems go to [SECURITY.md](SECURITY.md)**, never a public issue.

## Where things are

- `src/art30_emit/emit.py` — `declare`, `emit` and the mapping onto OpenLineage facets.
- `src/art30_emit/__main__.py` — the `art30-emit … -- <command>` wrapper.
- `tests/` — `test_emit.py` for the events, `test_cli.py` for the wrapper.
- `examples/nightly-export/` and `tools/capture_example.py` — the worked example and the
  script that captures its transcript.

Python 3.12 is the floor; do not add workarounds for older versions.
