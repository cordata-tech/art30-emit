# Contributing

Issues and pull requests are welcome. If you work with a coding agent, point it at
[AGENTS.md](AGENTS.md), the short form of this page; this one gives the reasons.

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
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/codespell
```

`pre-commit install`, once, runs ruff, codespell and a few file checks before each
commit, at the same versions CI pins in the `dev` extra.

The worked example needs `qedro` as well, and CI checks that its transcript still
matches what the commands print:

```bash
uv pip install qedro
python tools/capture_example.py --check
```

If it fails because the output genuinely changed, rerun without `--check` and
commit the result. The transcript is captured rather than written, so that a
claim on the front page cannot quietly stop being true.

## Commits and pull requests

**Explain the reasoning, not the diff.** A commit message here is for the person who
finds this code in a year and wants to know why it is shaped this way.

**Sign your commits.** `git config commit.gpgsign true` with an SSH or GPG key. A
package about provenance that accepts unsigned commits is making a point it would rather
not, and `main` refuses them.

**Sign off every commit, too** — `git commit -s`, which adds `Signed-off-by: Your Name
<you@example.com>`. It certifies, under the [Developer Certificate of
Origin](https://developercertificate.org), that you wrote the change or otherwise have the
right to submit it under Apache-2.0. It is the lightweight alternative to a contributor
licence agreement that the Linux kernel and the Linux Foundation's projects use,
OpenLineage among them. The DCO check fails a pull request with a commit whose sign-off
does not match its author; `git rebase --signoff main` adds the missing ones. Signing and
signing off are different things: the signature proves who made the commit, the sign-off
is what they certify about it.

**Coding agents are welcome.** Saying that one helped is welcome too, though not
required: a line in the pull request on what it did and what you checked yourself tells
a reviewer where to look harder, and a commit trailer such as `Assisted-by: <tool>`, or
the `Co-Authored-By:` line many tools add on their own, is fine. Whoever opens the pull
request is responsible for every line in it, whatever wrote it, and has read every one.

**How a change gets in.** Fork, branch, open a pull request against `main`. A merge needs
CI to pass on Python 3.12, 3.13 and 3.14, the DCO and workflow checks, and an approving
review from a code owner given after the last push; `main` takes no force pushes and
cannot be deleted. `.github/CODEOWNERS` requests that review automatically, and lists
separately the paths where a change is easy to make and expensive to get wrong — the
facet key and schema URL, how a declaration becomes facets, how the wrapper runs a
command, the dependencies and the release workflow. A pull request touching one of those
is worth a sentence in its description about which rule above it keeps. Release tags are
created by maintainers only.

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
