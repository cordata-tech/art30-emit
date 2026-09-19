# What the example produced

Captured by `tools/capture_example.py`, not written by hand. The run id and the
event timestamps are replaced with `<run-id>` and `<timestamp>` because they
change on every run; everything else is what the commands printed.

## Emitting

```console
$ ART30_EMIT_FILE=events.jsonl python export.py
exported 4 rows
```

The first event, reformatted for reading:

```json
{
  "eventTime": "<timestamp>",
  "eventType": "START",
  "inputs": [
    {
      "facets": {
        "tags": {
          "_producer": "https://github.com/cordata-tech/art30-emit",
          "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/TagsDatasetFacet.json#/$defs/TagsDatasetFacet",
          "tags": [
            {
              "key": "data_category",
              "source": "USER",
              "value": "contact"
            },
            {
              "key": "subject_type",
              "source": "USER",
              "value": "customer"
            },
            {
              "key": "residency",
              "source": "USER",
              "value": "eu"
            },
            {
              "key": "retention",
              "source": "USER",
              "value": "P7Y"
            }
          ]
        }
      },
      "inputFacets": {},
      "name": "crm_curated.consent_state",
      "namespace": "warehouse"
    }
  ],
  "job": {
    "facets": {
      "processing": {
        "_producer": "https://github.com/cordata-tech/art30-emit",
        "_schemaURL": "https://github.com/cordata-tech/qedro/blob/main/schemas/openlineage-art30-processing-facet.json",
        "legal_basis": "contract",
        "purpose": "customer-administration"
      }
    },
    "name": "nightly-consent-export",
    "namespace": "acme.crm"
  },
  "outputs": [
    {
      "facets": {
        "tags": {
          "_producer": "https://github.com/cordata-tech/art30-emit",
          "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/TagsDatasetFacet.json#/$defs/TagsDatasetFacet",
          "tags": [
            {
              "key": "data_category",
              "source": "USER",
              "value": "contact"
            },
            {
              "key": "subject_type",
              "source": "USER",
              "value": "customer"
            },
            {
              "key": "residency",
              "source": "USER",
              "value": "eu"
            },
            {
              "key": "retention",
              "source": "USER",
              "value": "P30D"
            }
          ]
        }
      },
      "name": "consent/nightly.csv",
      "namespace": "s3://acme-exports",
      "outputFacets": {}
    }
  ],
  "producer": "https://github.com/cordata-tech/art30-emit",
  "run": {
    "facets": {
      "tags": {
        "_producer": "https://github.com/cordata-tech/art30-emit",
        "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/TagsRunFacet.json#/$defs/TagsRunFacet",
        "tags": [
          {
            "key": "openlineage_client_version",
            "source": "OPENLINEAGE_CLIENT",
            "value": "1.53.0"
          }
        ]
      }
    },
    "runId": "<run-id>"
  },
  "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"
}
```

## Reading it back as a record of processing activities

```console
$ qedro ropa . --config qedro.yaml
Record of processing activities — ACME Finanz GmbH
  contact: datenschutz@acme-finanz.example

  acme.crm/nightly-consent-export
    purpose       customer-administration
    legal basis   contract
    categories    contact
    subjects      customer
    residency     eu
    retention     P30D, P7Y
    recipients    Versandpartner Nord GmbH, as processor for postal consent notices
                  (declared)
    security      the export is encrypted at rest and deleted after 30 days; access
                  limited to the CRM domain's engineers (declared)
    reads         warehouse/crm_curated.consent_state
    writes        s3://acme-exports/consent/nightly.csv
    runs          1 in window, last <timestamp>

  Scope of this record
    source        .
    window        <timestamp> to <timestamp>
    in view       1 jobs, 2 datasets, 2 events
    namespaces    acme.crm
    provenance    1 evidenced, 0 from the mapping file, 0 undeclared
    reported      (c) categories of data subjects and of personal data: 1 of 1 activity,
                  (e) transfers to third countries: 1 of 1 activity, (f) time limits for
                  erasure: 1 of 1 activity
    Art. 30(1)    this record has fields for (a) the controller, (b) the purposes, (c)
                  categories of data subjects and of personal data, (d) categories of
                  recipients, (e) transfers to third countries, (f) time limits for
                  erasure and (g) security measures — (d) and (g) can only be declared,
                  because no lineage carries either and nothing here evidences them
    domains       crm from a mapping rule
    This record covers processing performed by pipelines that emit lineage, and any
    activities declared with no lineage. Systems that do not emit lineage — CRM, HR,
    ticketing, marketing tools, anything on paper — are not represented here unless they
    are declared, a declared activity is an assertion rather than evidence, and the
    absence of anything else from this record is not evidence of its absence from the
    organisation.

  every activity stands on emitted evidence   ∎
```

The tombstone on the last line is Qedro's, and it is withheld rather than
printed whenever a purpose or a legal basis came from a mapping file instead of
an emitted facet. Here every field in the record above the `recipients` and
`security` lines came out of the events this package emitted, which is why the
record claims to be a proof. The two exceptions are marked `(declared)`, because
no lineage carries a recipient or a security measure and a record that implied
otherwise would be lying about its own evidence.
