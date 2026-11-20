# art30-emit — working notes

@AGENTS.md

The rules above bind every contributor and agent. What follows is the maintainer's
working context.

- **Commit identity is `laszlo@cordata.tech`, signed**, with no assistant commit trailers.
  `jj` is colocated with git: work in `jj` and let it write the git commits. The
  maintainer commits to `main` directly, through the admin bypass in the `main` ruleset;
  outside contributors use pull requests.
- **Pushing a `v*` tag publishes to PyPI** through trusted publishing, so a tag is a
  release decision. `workflow_dispatch` on `release.yml` is the dry run.
- **The facet belongs to qedro.** Its schema is generated there from
  `pipeline_runtime.descriptor.Processing`; a field change starts in pipeline-runtime,
  reaches qedro's schema, and only then lands here. When that changes, check the
  README's examples and the worked example's transcript against it.
