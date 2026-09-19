from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[], list[dict]]:
    """Send events to a file, and read them back as dictionaries.

    The file transport is the one the package documents for a first run, so the
    tests exercise the path a reader is told to try rather than a stub of it.
    """
    target = tmp_path / "events.jsonl"
    monkeypatch.setenv("ART30_EMIT_FILE", str(target))
    monkeypatch.delenv("OPENLINEAGE_URL", raising=False)
    monkeypatch.delenv("OPENLINEAGE_CONFIG", raising=False)

    def read() -> list[dict]:
        if not target.exists():
            return []
        return [json.loads(line) for line in target.read_text().splitlines() if line.strip()]

    return read
