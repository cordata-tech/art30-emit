# Security

## Reporting

Email **privacy@cordata.tech**, or open a private advisory through GitHub's
*Report a vulnerability* on this repository. Please do not open a public issue
for anything exploitable.

Expect an acknowledgement within three working days. If a fix is warranted it
ships as a patch release with an entry in the changelog naming what was wrong;
credit is given unless you would rather it were not.

Supported: the most recent `0.x` release. There is no long-term support branch
before `1.0`.

## What this package can reach

Worth stating plainly, because it is short and it is the answer to most of the
questions a review will ask.

**It sends events and reads nothing.** The one runtime dependency is
`openlineage-python`, and where events go is that client's decision — through
`OPENLINEAGE_URL`, `OPENLINEAGE_CONFIG`, or `ART30_EMIT_FILE` for a local file.
This package invents no transport, opens no connection of its own, and has no
credential.

**The command wrapper runs what it is given.** `art30-emit … -- <command>`
executes that command with `subprocess.run` and no shell, so nothing is
interpreted: an argument containing `;` or `$(…)` is an argument. It forwards the
exit status and emits a `FAIL` event for a non-zero one.

**It decides nothing about your data.** No validation against a compiled list of
purposes, no legal basis inferred from a job name, no default filling a field
nobody declared. What the caller passes is what goes on the wire.

## What goes on the wire

Whatever you put in the declaration: a job name, dataset names, a purpose, a
lawful basis, and any classification tags you pass. That is metadata about
processing rather than personal data — but it is *your* metadata, and a job name
or a dataset key can be revealing on its own. Where those events go is worth the
same review as any other lineage you emit.
