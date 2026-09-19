from __future__ import annotations

import sys
from collections.abc import Callable

import pytest

from art30_emit.__main__ import _classify, main


def _run(*args: str) -> int:
    return main(list(args))


def test_the_command_runs_and_its_output_is_untouched(
    events: Callable[[], list[dict]], capfd: pytest.CaptureFixture[str]
) -> None:
    assert _run("--job", "demo/hello", "--", sys.executable, "-c", "print('hi')") == 0
    assert "hi" in capfd.readouterr().out
    assert [event["eventType"] for event in events()] == ["START", "COMPLETE"]


def test_a_non_zero_exit_emits_fail_and_is_forwarded(events: Callable[[], list[dict]]) -> None:
    code = _run("--job", "demo/hello", "--", sys.executable, "-c", "raise SystemExit(3)")

    assert code == 3
    assert [event["eventType"] for event in events()] == ["START", "FAIL"]
    assert "exited 3" in events()[-1]["run"]["facets"]["errorMessage"]["message"]


def test_a_command_that_does_not_exist_emits_fail(events: Callable[[], list[dict]]) -> None:
    with pytest.raises(SystemExit):
        _run("--job", "demo/hello", "--", "definitely-not-a-command-8d3f")

    assert [event["eventType"] for event in events()] == ["START", "FAIL"]


def test_the_declaration_reaches_the_event(events: Callable[[], list[dict]]) -> None:
    _run(
        "--job", "acme.billing/monthly-invoices",
        "--purpose", "contract-performance",
        "--legal-basis", "contract",
        "--reads", "warehouse/billing_raw.usage",
        "--writes", "warehouse/billing_curated.invoices",
        "--tag", "warehouse/billing_curated.invoices:data_category=financial",
        "--", sys.executable, "-c", "pass",
    )  # fmt: skip

    start = events()[0]
    assert start["job"]["namespace"] == "acme.billing"
    assert start["job"]["name"] == "monthly-invoices"
    assert start["job"]["facets"]["processing"]["purpose"] == "contract-performance"
    assert [d["name"] for d in start["inputs"]] == ["billing_raw.usage"]
    tags = start["outputs"][0]["facets"]["tags"]["tags"]
    assert [tag["value"] for tag in tags] == ["financial"]


def test_nothing_to_run_is_an_error(events: Callable[[], list[dict]]) -> None:
    with pytest.raises(SystemExit, match="after --"):
        _run("--job", "demo/hello")

    assert events() == []


@pytest.mark.parametrize(
    "pair",
    ["no-colon", "dataset:no-equals", "dataset:=value", ":key=value", "dataset:key="],
)
def test_a_malformed_tag_says_what_the_shape_should_be(pair: str) -> None:
    with pytest.raises(SystemExit, match="dataset:key=value"):
        _classify([pair])


def test_tags_for_one_dataset_accumulate() -> None:
    assert _classify(["d/one:a=1", "d/one:b=2", "d/two:a=3"]) == {
        "d/one": {"a": "1", "b": "2"},
        "d/two": {"a": "3"},
    }


def test_a_uri_dataset_survives_the_tag_syntax() -> None:
    """The colons in `s3://…` belong to the dataset, not to the separator."""
    assert _classify(["s3://acme-exports/consent/nightly.csv:residency=eu"]) == {
        "s3://acme-exports/consent/nightly.csv": {"residency": "eu"}
    }


def test_a_value_may_contain_spaces_and_commas() -> None:
    assert _classify(["d/one:purpose=fraud detection, and reporting"]) == {
        "d/one": {"purpose": "fraud detection, and reporting"}
    }
