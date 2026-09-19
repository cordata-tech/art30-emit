# art30-emit

Put the OpenLineage **Art. 30 processing facet** on the wire from code that emits
nothing today.

dbt, Airflow, Spark and Flink all emit OpenLineage, and none of them emits
`purpose` or `legal_basis`. Everything else a record of processing activities needs
— what ran, what it read, what it wrote, when, and in some cases what the data is —
can be evidenced from what an organisation already runs. Those two fields cannot, so
they end up asserted in a spreadsheet beside the code and drift from it within a
quarter.

This package emits them from the thing that ran, for the systems nobody instruments:
a Lambda, a stored procedure behind a shell wrapper, a cron job, a notebook that
matters more than it should.

## Install

```bash
pip install art30-emit
```

One runtime dependency, `openlineage-python`. Python 3.12 or later.

## Use it as a context manager

```python
from art30_emit import declare

with declare(
    "acme.crm/consent-sync",
    purpose="customer-administration",
    legal_basis="contract",
    reads=["warehouse/crm_raw.consent_events"],
    writes=["warehouse/crm_curated.consent_state"],
    classify={
        "warehouse/crm_curated.consent_state": {
            "data_category": "contact",
            "subject_type": "customer",
            "residency": "eu",
            "retention": "P7Y",
        }
    },
):
    sync_consent()
```

`START` is emitted on entry and `COMPLETE` on exit. An exception emits `FAIL` with
the error message and stack trace, then continues to propagate: a record of what
happened must not change what happens.

## Use it as a command wrapper

The wrapper reaches work an import cannot — a stored procedure called from a shell
script, an SSIS step, a binary somebody compiled in 2014.

```bash
art30-emit \
    --job acme.billing/monthly-invoices \
    --purpose contract-performance \
    --legal-basis contract \
    --reads warehouse/billing_raw.usage \
    --writes warehouse/billing_curated.invoices \
    --tag warehouse/billing_curated.invoices:data_category=financial \
    --tag warehouse/billing_curated.invoices:subject_type=customer \
    -- ./run-invoicing.sh
```

The command runs unchanged and its exit status is forwarded. A non-zero status emits
`FAIL` rather than `COMPLETE`, so a record built from these events can tell an
auditor which runs finished.

## Where the events go

Wherever the OpenLineage client is configured to send them, through
`OPENLINEAGE_URL` or `OPENLINEAGE_CONFIG` as that client documents. A transport this
package invented would be one more thing to trust.

For a first run, with neither set, `ART30_EMIT_FILE` appends the events to a file so
you can read what was produced:

```bash
ART30_EMIT_FILE=events.jsonl art30-emit --job demo/hello --purpose demonstration \
    --legal-basis consent -- echo hello
```

## Two rules it keeps

**It emits the published facet, not one of its own.** The schema is
[`openlineage-art30-processing-facet.json`](https://github.com/cordata-tech/qedro/blob/main/schemas/openlineage-art30-processing-facet.json),
generated from a governance model rather than written beside it, and the
classification rides on the standard `tags` dataset facet (spec 1-0-0) rather than a
private key. A second spelling of the same fields would be a private vocabulary
wearing a standard's clothes.

**It never decides anything.** No validation against a compiled list of purposes, no
guessing a legal basis from a job name, no default that fills a field nobody
declared. What the caller says is what goes on the wire, and what the caller does not
say is absent — which is the state a record has to be able to report, because *nobody
said* and *we say it is none* are different answers to an auditor.

## What reads it

Any governance layer that reads OpenLineage. [Qedro](https://github.com/cordata-tech/qedro)
turns these events into a GDPR Art. 30 record of processing activities, and
[`pipeline-runtime`](https://github.com/cordata-tech/pipeline-runtime) emits the same
facet from pipelines it executes — this is the second implementation of that schema
rather than a second definition of it.

## Licence

Apache-2.0.
