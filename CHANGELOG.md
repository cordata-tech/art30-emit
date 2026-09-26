# Changelog

Notable changes, in the words of somebody deciding whether to upgrade.

`0.x` may change interfaces between releases. The one part that will not move
without a major version is what goes on the wire: the `processing` facet's key and
schema URL, and the use of the standard `tags` dataset facet for classification,
because a consumer's record depends on both.

## 0.1.0 — 2026-09-26

The first version, and the whole of it: put the Art. 30 facet on the wire from code
no OpenLineage integration can reach.

- **`declare(...)` as a context manager**, emitting `START` on entry and `COMPLETE`
  on exit. An exception emits `FAIL` with the message and stack trace in the standard
  `errorMessage` run facet, then propagates unchanged — a record of what happened must
  not change what happens.
- **`art30-emit … -- <command>` as a wrapper**, for the work an import cannot reach:
  a stored procedure behind a shell script, an SSIS step, a binary compiled in 2014.
  The command's exit status is forwarded, and a non-zero one emits `FAIL` rather than
  `COMPLETE`.
- **`purpose` and `legal_basis` in the published `processing` facet**, under the
  schema generated in `cordata-tech/qedro` from a governance model. This is the second
  implementation of that schema rather than a second definition of it.
- **Classification on the standard `tags` dataset facet** (spec 1-0-0), per dataset,
  with `source: USER` — because somebody wrote it down by hand, which is the
  distinction a record carries through to its output. That is what lets Art. 30(1)(c),
  (e) and (f) be reported for systems that could otherwise only be asserted.
- **A field nobody declared is absent, never empty.** *Nobody said* and *we say it is
  none* are different answers to an auditor, and only the first can be corrected.
- **Nothing is decided here**: no validation against a compiled list of purposes, no
  legal basis guessed from a job name, no default filling a field nobody declared.
- **URI namespaces stay whole.** `s3://acme-exports/consent/nightly.csv` is namespace
  `s3://acme-exports` and name `consent/nightly.csv`, in the library and in `--tag`.
- **A worked example with a captured transcript**, `examples/nightly-export`: a cron
  script wrapped in `declare`, read back by Qedro into a record that earns its
  tombstone. `tools/capture_example.py --check` runs in CI, so the transcript fails
  the build rather than going quietly stale.
