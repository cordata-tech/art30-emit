"""The command wrapper.

    art30-emit --job acme.crm/consent-sync \\
        --purpose customer-administration --legal-basis contract \\
        --reads warehouse/crm_raw.consent_events \\
        --writes warehouse/crm_curated.consent_state \\
        -- python sync.py

The wrapper exists for the work an import cannot reach: a stored procedure
called from a shell script, a cron job, an SSIS step, a binary somebody compiled
in 2014. It runs the command unchanged, forwards its exit status, and emits FAIL
rather than COMPLETE when that status is non-zero.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence

from openlineage.client.event_v2 import RunState

from . import __version__
from .emit import Declaration, emit


class CommandFailed(Exception):
    """A non-zero exit, carried into the FAIL event as its message."""


def _classify(pairs: Sequence[str]) -> dict[str, dict[str, str]]:
    """`dataset:key=value` into `{dataset: {key: value}}`.

    Repeated for each tag rather than a single JSON blob, so a value with a
    comma or a space in it needs no quoting rules of our own.

    The dataset is taken up to the *last* colon and the value from the *first*
    equals sign, because a dataset key is often a URI — `s3://acme-exports/…` —
    and a tag key is never either.
    """
    out: dict[str, dict[str, str]] = {}
    for pair in pairs:
        left, equals, value = pair.partition("=")
        dataset, sep, key = left.rpartition(":")
        if not (sep and equals and dataset and key and value):
            raise SystemExit(
                f"--tag {pair!r} should be `dataset:key=value`, for example "
                "`warehouse/crm_raw.contacts:data_category=contact`"
            )
        out.setdefault(dataset, {})[key] = value
    return out


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="art30-emit",
        description="Run a command and emit the OpenLineage Art. 30 processing facet around it.",
        epilog=(
            "Where the events go is the OpenLineage client's decision: set OPENLINEAGE_URL "
            "or OPENLINEAGE_CONFIG. With neither, set ART30_EMIT_FILE to append them to a "
            "file, which is enough to read what a first run produced."
        ),
    )
    parser.add_argument("--version", action="version", version=f"art30-emit {__version__}")
    parser.add_argument(
        "--job",
        required=True,
        metavar="NAMESPACE/NAME",
        help="what ran, for example acme.crm/consent-sync",
    )
    parser.add_argument(
        "--purpose",
        default="",
        help="Art. 30(1)(b), the purpose of the processing; omitted if not given",
    )
    parser.add_argument(
        "--legal-basis",
        default="",
        help="the lawful basis under Art. 6(1); omitted if not given",
    )
    parser.add_argument(
        "--reads",
        action="append",
        default=[],
        metavar="NAMESPACE/NAME",
        help="an input dataset; repeat for several",
    )
    parser.add_argument(
        "--writes",
        action="append",
        default=[],
        metavar="NAMESPACE/NAME",
        help="an output dataset; repeat for several",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        metavar="DATASET:KEY=VALUE",
        help=(
            "a classification for one of those datasets, emitted as the standard tags "
            "facet; repeat for several"
        ),
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="reuse an existing run id instead of generating one",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="-- followed by the command to run",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("nothing to run: put the command after --")

    declaration = Declaration(
        job=args.job,
        purpose=args.purpose,
        legal_basis=args.legal_basis,
        reads=tuple(args.reads),
        writes=tuple(args.writes),
        classify=_classify(args.tag),
        run_id=args.run_id,
    )

    emit(declaration, RunState.START)
    try:
        # Running whatever the caller named is the point; check=False because a
        # non-zero exit is a FAIL event to emit, not an exception to raise here.
        completed = subprocess.run(command, check=False)
    except OSError as error:
        emit(declaration, RunState.FAIL, error=error)
        raise SystemExit(f"{command[0]}: {error}") from error

    if completed.returncode:
        emit(
            declaration,
            RunState.FAIL,
            error=CommandFailed(f"{command[0]} exited {completed.returncode}"),
        )
    else:
        emit(declaration, RunState.COMPLETE)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
