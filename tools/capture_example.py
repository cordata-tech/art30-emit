"""Run the worked example and write down what it printed.

The transcript is evidence that the claim on the front page holds — events from
this package become a record that stands on emitted evidence — so it is captured
rather than written, and `--check` fails when the captured file and a fresh run
disagree.

Two fields are replaced before comparison, because they change on every run and
nothing in the claim depends on them: the run id and the event timestamps. The
replacement is visible in the transcript itself, so nobody reads a placeholder as
a real value.

    python tools/capture_example.py            # rewrite the transcript
    python tools/capture_example.py --check    # fail if it is stale

Needs `qedro` on PATH (`pip install qedro`); without it the script says so and
exits non-zero rather than writing half a transcript.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "nightly-export"
TRANSCRIPT = EXAMPLE / "transcript.md"
EVENTS = EXAMPLE / "events.jsonl"

RUN_ID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
TIMESTAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00\b")

HEADER = """# What the example produced

Captured by `tools/capture_example.py`, not written by hand. The run id and the
event timestamps are replaced with `<run-id>` and `<timestamp>` because they
change on every run; everything else is what the commands printed.

## Emitting

```console
$ ART30_EMIT_FILE=events.jsonl python export.py
{emit}```

The first event, reformatted for reading:

```json
{event}
```

## Reading it back as a record of processing activities

```console
$ qedro ropa . --config qedro.yaml
{ropa}```

The tombstone on the last line is Qedro's, and it is withheld rather than
printed whenever a purpose or a legal basis came from a mapping file instead of
an emitted facet. Here every field in the record above the `recipients` and
`security` lines came out of the events this package emitted, which is why the
record claims to be a proof. The two exceptions are marked `(declared)`, because
no lineage carries a recipient or a security measure and a record that implied
otherwise would be lying about its own evidence.
"""


def _stable(text: str) -> str:
    return TIMESTAMP.sub("<timestamp>", RUN_ID.sub("<run-id>", text))


def _run(command: list[str], **env: str) -> str:
    result = subprocess.run(
        command,
        cwd=EXAMPLE,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ | env,
    )
    if result.returncode:
        sys.exit(f"{' '.join(command)} exited {result.returncode}:\n{result.stderr}")
    return result.stdout


def capture() -> str:
    if shutil.which("qedro") is None:
        sys.exit("qedro is not on PATH — `pip install qedro` and run this again")

    EVENTS.unlink(missing_ok=True)
    source = str(Path(__file__).resolve().parent.parent / "src")
    emit = _run(
        [sys.executable, "export.py"],
        ART30_EMIT_FILE=str(EVENTS.name),
        PYTHONPATH=source,
    )

    first = json.loads(EVENTS.read_text().splitlines()[0])
    ropa = _run(["qedro", "ropa", ".", "--config", "qedro.yaml"])

    return HEADER.format(
        emit=_stable(emit),
        event=_stable(json.dumps(first, indent=2, sort_keys=True)),
        ropa=_stable(ropa),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the worked example and write down what it printed."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed transcript differs from a fresh run",
    )
    args = parser.parse_args()

    fresh = capture()
    if args.check:
        current = TRANSCRIPT.read_text() if TRANSCRIPT.exists() else ""
        if current != fresh:
            sys.exit(
                f"{TRANSCRIPT.name} is stale — run `python tools/capture_example.py` "
                "and commit the result"
            )
        print(f"{TRANSCRIPT.name} matches a fresh run")
        return 0

    TRANSCRIPT.write_text(fresh)
    print(f"wrote {TRANSCRIPT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
