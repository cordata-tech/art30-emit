"""Building and sending the events.

The shape is the smallest thing that answers an auditor's question: one job, one
run, START when the work begins and COMPLETE or FAIL when it ends, with the
purpose and lawful basis on the job and the classification on the datasets.

Everything about where events go is the client's business, not this module's.
``OPENLINEAGE_URL``, ``OPENLINEAGE_CONFIG`` and the rest are documented by the
OpenLineage client and work here unchanged, because a transport this package
invented would be one more thing to trust.
"""

from __future__ import annotations

import os
import traceback
import uuid
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import attr
from openlineage.client import OpenLineageClient
from openlineage.client.event_v2 import (
    InputDataset,
    Job,
    OutputDataset,
    Run,
    RunEvent,
    RunState,
    set_producer,
)
from openlineage.client.facet_v2 import JobFacet, error_message_run
from openlineage.client.generated import tags_dataset
from openlineage.client.transport.file import FileConfig, FileTransport

#: Every event says which version of what produced it. A consumer weighing an
#: event it did not expect can then find out what wrote it.
PRODUCER = "https://github.com/cordata-tech/art30-emit"

#: How a tag says where it came from. `USER` rather than a catalog's name,
#: because somebody wrote this classification down by hand — which is the whole
#: distinction the record carries through to its output.
TAG_SOURCE = "USER"


@attr.define
class ProcessingJobFacet(JobFacet):
    """The Art. 30 fields, on the job that performs the processing.

    A job facet rather than a run facet, because a purpose is a property of the
    pipeline and not of one execution of it. The schema is the one published in
    cordata-tech/qedro and implemented by cordata-tech/pipeline-runtime; this is
    the second implementation of it, not a second definition.
    """

    purpose: str
    legal_basis: str

    @staticmethod
    def _get_schema() -> str:
        from . import FACET_SCHEMA

        return FACET_SCHEMA


@dataclass
class Declaration:
    """What one piece of work declares about itself.

    `reads` and `writes` are `namespace/name` — the same spelling the record
    prints, and the OpenLineage naming conventions describe. `classify` maps one
    of those to the tags that apply to it, which is how an Art. 30 record learns
    the categories, data subjects, residency and retention it cannot otherwise
    evidence for this system.
    """

    job: str
    purpose: str = ""
    legal_basis: str = ""
    reads: Sequence[str] = field(default_factory=tuple)
    writes: Sequence[str] = field(default_factory=tuple)
    classify: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    run_id: str = ""

    def __post_init__(self) -> None:
        if "/" not in self.job:
            raise ValueError(
                f"job {self.job!r} should be `namespace/name`, for example "
                "`acme.crm/consent-sync`: a name without a namespace is not an identity"
            )
        self.run_id = self.run_id or str(uuid.uuid4())

    @property
    def namespace(self) -> str:
        return split(self.job)[0]

    @property
    def name(self) -> str:
        return split(self.job)[1]


def client() -> OpenLineageClient:
    """Where events go, as the OpenLineage client decides it.

    `OPENLINEAGE_URL` or `OPENLINEAGE_CONFIG` configure a real backend. With
    neither, and `ART30_EMIT_FILE` set, events are appended to that file — which
    is what makes a first run readable without standing anything up, and what the
    tests here use.
    """
    target = os.environ.get("ART30_EMIT_FILE")
    if target and not (os.environ.get("OPENLINEAGE_URL") or os.environ.get("OPENLINEAGE_CONFIG")):
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        return OpenLineageClient(
            transport=FileTransport(FileConfig(log_file_path=str(path), append=True))
        )
    return OpenLineageClient()


def split(key: str) -> tuple[str, str]:
    """`namespace/name`, with a URI namespace kept whole.

    OpenLineage's naming conventions make the namespace a scheme and authority
    for anything addressable — `s3://acme-exports`, `postgres://db:5432` — and
    the name the path within it. Splitting on the first slash would turn `s3` into
    the namespace and hand a record a dataset nobody can find again.
    """
    scheme, marker, rest = key.partition("://")
    if marker:
        authority, _, name = rest.partition("/")
        return f"{scheme}://{authority}", name
    namespace, _, name = key.partition("/")
    return namespace, name


def _datasets(declaration: Declaration, keys: Sequence[str], cls: Any) -> list[Any]:
    out = []
    for key in keys:
        namespace, name = split(key)
        if not name:
            raise ValueError(
                f"dataset {key!r} should be `namespace/name`, for example "
                "`warehouse/crm_raw.contacts` or `s3://acme-exports/consent/nightly.csv`"
            )
        facets: dict[str, Any] = {}
        tags = declaration.classify.get(key)
        if tags:
            facets["tags"] = tags_dataset.TagsDatasetFacet(
                tags=[
                    tags_dataset.TagsDatasetFacetFields(key=k, value=v, source=TAG_SOURCE)
                    for k, v in tags.items()
                ]
            )
        out.append(cls(namespace=namespace, name=name, facets=facets))
    return out


def _event(
    declaration: Declaration,
    state: RunState,
    *,
    error: BaseException | None = None,
) -> RunEvent:
    job_facets: dict[str, Any] = {}
    # Absent rather than empty when nobody declared one. A record can report
    # *nobody said*; it cannot report an empty string as anything at all.
    if declaration.purpose or declaration.legal_basis:
        job_facets["processing"] = ProcessingJobFacet(
            purpose=declaration.purpose, legal_basis=declaration.legal_basis
        )

    run_facets: dict[str, Any] = {}
    if error is not None:
        run_facets["errorMessage"] = error_message_run.ErrorMessageRunFacet(
            message=str(error) or type(error).__name__,
            programmingLanguage="PYTHON",
            stackTrace="".join(traceback.format_exception(error)),
        )

    return RunEvent(
        eventType=state,
        eventTime=datetime.now(UTC).isoformat(),
        run=Run(runId=declaration.run_id, facets=run_facets),
        job=Job(namespace=declaration.namespace, name=declaration.name, facets=job_facets),
        # Datasets on every event, including the terminal one. Flink's
        # integration names them only on START, and a consumer then has to
        # gather them across a job's events to know what it touched.
        inputs=_datasets(declaration, declaration.reads, InputDataset),
        outputs=_datasets(declaration, declaration.writes, OutputDataset),
    )


def emit(declaration: Declaration, state: RunState, *, error: BaseException | None = None) -> None:
    """Send one event. Exposed because a caller may already have its own run loop."""
    set_producer(PRODUCER)
    client().emit(_event(declaration, state, error=error))


@contextmanager
def declare(
    job: str,
    *,
    purpose: str = "",
    legal_basis: str = "",
    reads: Sequence[str] = (),
    writes: Sequence[str] = (),
    classify: Mapping[str, Mapping[str, str]] | None = None,
    run_id: str = "",
) -> Generator[Declaration]:
    """Emit START around a piece of work, and COMPLETE or FAIL after it.

        with declare("acme.crm/consent-sync", purpose="customer-administration",
                     legal_basis="contract", reads=["warehouse/crm_raw.consent_events"],
                     writes=["warehouse/crm_curated.consent_state"]):
            sync_consent()

    A failure emits FAIL with the error, and the exception continues: a record of
    what happened must not change what happens.
    """
    declaration = Declaration(
        job=job,
        purpose=purpose,
        legal_basis=legal_basis,
        reads=tuple(reads),
        writes=tuple(writes),
        classify=dict(classify or {}),
        run_id=run_id,
    )
    emit(declaration, RunState.START)
    try:
        yield declaration
    # Broad on purpose, and re-raised below: KeyboardInterrupt and SystemExit
    # end a run too, and a record that omitted them would be wrong.
    except BaseException as error:
        emit(declaration, RunState.FAIL, error=error)
        raise
    emit(declaration, RunState.COMPLETE)
