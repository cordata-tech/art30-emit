from __future__ import annotations

from collections.abc import Callable

import pytest

from art30_emit import FACET_KEY, FACET_SCHEMA, Declaration, declare
from art30_emit.emit import split


def test_a_completed_run_emits_start_then_complete(events: Callable[[], list[dict]]) -> None:
    with declare("acme.crm/consent-sync", purpose="customer-administration"):
        pass

    assert [event["eventType"] for event in events()] == ["START", "COMPLETE"]


def test_both_events_carry_the_same_run_id(events: Callable[[], list[dict]]) -> None:
    with declare("acme.crm/consent-sync"):
        pass

    start, complete = events()
    assert start["run"]["runId"] == complete["run"]["runId"]


def test_the_facet_carries_the_declared_fields_and_the_published_schema(
    events: Callable[[], list[dict]],
) -> None:
    with declare(
        "acme.crm/consent-sync", purpose="customer-administration", legal_basis="contract"
    ):
        pass

    facet = events()[0]["job"]["facets"][FACET_KEY]
    assert facet["purpose"] == "customer-administration"
    assert facet["legal_basis"] == "contract"
    assert facet["_schemaURL"] == FACET_SCHEMA


def test_a_field_nobody_declared_is_absent_rather_than_empty(
    events: Callable[[], list[dict]],
) -> None:
    """*Nobody said* and *we say it is none* are different answers to an auditor."""
    with declare("acme.crm/consent-sync"):
        pass

    assert FACET_KEY not in events()[0]["job"]["facets"]


def test_datasets_are_split_by_direction(events: Callable[[], list[dict]]) -> None:
    with declare(
        "acme.crm/consent-sync",
        reads=["warehouse/crm_raw.consent_events"],
        writes=["warehouse/crm_curated.consent_state"],
    ):
        pass

    start = events()[0]
    assert [d["name"] for d in start["inputs"]] == ["crm_raw.consent_events"]
    assert [d["name"] for d in start["outputs"]] == ["crm_curated.consent_state"]
    assert start["inputs"][0]["namespace"] == "warehouse"


def test_datasets_are_named_on_the_terminal_event_too(events: Callable[[], list[dict]]) -> None:
    """A consumer should not have to gather a job's datasets across its events."""
    with declare("acme.crm/consent-sync", writes=["warehouse/crm_curated.consent_state"]):
        pass

    assert [d["name"] for d in events()[-1]["outputs"]] == ["crm_curated.consent_state"]


def test_classification_rides_on_the_standard_tags_facet(
    events: Callable[[], list[dict]],
) -> None:
    with declare(
        "acme.crm/consent-sync",
        writes=["warehouse/crm_curated.consent_state"],
        classify={
            "warehouse/crm_curated.consent_state": {
                "data_category": "contact",
                "subject_type": "customer",
            }
        },
    ):
        pass

    facet = events()[0]["outputs"][0]["facets"]["tags"]
    assert "openlineage.io/spec/facets/1-0-0/TagsDatasetFacet" in facet["_schemaURL"]
    assert {tag["key"]: tag["value"] for tag in facet["tags"]} == {
        "data_category": "contact",
        "subject_type": "customer",
    }
    assert {tag["source"] for tag in facet["tags"]} == {"USER"}


def test_an_unclassified_dataset_carries_no_tags_facet(events: Callable[[], list[dict]]) -> None:
    with declare("acme.crm/consent-sync", writes=["warehouse/crm_curated.consent_state"]):
        pass

    assert "tags" not in events()[0]["outputs"][0]["facets"]


def test_a_failure_emits_fail_and_still_raises(events: Callable[[], list[dict]]) -> None:
    """A record of what happened must not change what happens."""
    with pytest.raises(ZeroDivisionError), declare("acme.crm/consent-sync"):
        _ = 1 / 0

    emitted = events()
    assert [event["eventType"] for event in emitted] == ["START", "FAIL"]
    error = emitted[-1]["run"]["facets"]["errorMessage"]
    assert "division by zero" in error["message"]
    assert "ZeroDivisionError" in error["stackTrace"]


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("warehouse/crm_raw.contacts", ("warehouse", "crm_raw.contacts")),
        ("s3://acme-exports/consent/nightly.csv", ("s3://acme-exports", "consent/nightly.csv")),
        ("postgres://db:5432/public.contacts", ("postgres://db:5432", "public.contacts")),
    ],
)
def test_a_uri_namespace_is_kept_whole(key: str, expected: tuple[str, str]) -> None:
    """Splitting `s3://bucket/path` on the first slash names a dataset nobody can find."""
    assert split(key) == expected


def test_a_uri_dataset_reaches_the_event_whole(events: Callable[[], list[dict]]) -> None:
    with declare("acme.crm/export", writes=["s3://acme-exports/consent/nightly.csv"]):
        pass

    written = events()[0]["outputs"][0]
    assert written["namespace"] == "s3://acme-exports"
    assert written["name"] == "consent/nightly.csv"


def test_a_job_without_a_namespace_is_refused() -> None:
    with pytest.raises(ValueError, match="namespace"):
        Declaration(job="consent-sync")


def test_a_dataset_without_a_namespace_is_refused(events: Callable[[], list[dict]]) -> None:
    manager = declare("acme.crm/consent-sync", reads=["crm_raw.contacts"])
    with pytest.raises(ValueError, match="crm_raw.contacts"):
        manager.__enter__()

    assert events() == []


def test_a_caller_supplied_run_id_is_used(events: Callable[[], list[dict]]) -> None:
    with declare("acme.crm/consent-sync", run_id="00000000-0000-0000-0000-00000000beef"):
        pass

    assert events()[0]["run"]["runId"] == "00000000-0000-0000-0000-00000000beef"


def test_the_producer_names_this_package(events: Callable[[], list[dict]]) -> None:
    with declare("acme.crm/consent-sync"):
        pass

    assert events()[0]["producer"].endswith("art30-emit")
