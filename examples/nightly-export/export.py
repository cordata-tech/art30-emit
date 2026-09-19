"""A nightly export that emits no lineage, and what it takes to change that.

The shape is the one this package exists for: a script somebody wrote years ago,
scheduled by cron, reading one table and writing a file that leaves the company.
No orchestrator knows it exists, so no integration can emit for it, and the
record of processing activities has to assert its existence from a spreadsheet.

Wrapping the work in `declare` is the whole change. Everything below the context
manager is what the script already did.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from art30_emit import declare


def export(source: Path, target: Path) -> int:
    rows = list(csv.DictReader(source.open()))
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["customer_id", "email", "consent_state"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in rows)
    return len(rows)


def main() -> int:
    here = Path(__file__).parent
    with declare(
        "acme.crm/nightly-consent-export",
        # Art. 30(1)(b) and the lawful basis. Neither can be evidenced from
        # anything the script does, which is why they have to be declared here
        # rather than inferred somewhere downstream.
        purpose="customer-administration",
        legal_basis="contract",
        reads=["warehouse/crm_curated.consent_state"],
        writes=["s3://acme-exports/consent/nightly.csv"],
        # Art. 30(1)(c)–(f), on the datasets they describe. The processor
        # receiving the export is a recipient under (d), which no lineage can
        # carry, so it stays in qedro.yaml and is marked as declared.
        classify={
            "warehouse/crm_curated.consent_state": {
                "data_category": "contact",
                "subject_type": "customer",
                "residency": "eu",
                "retention": "P7Y",
            },
            "s3://acme-exports/consent/nightly.csv": {
                "data_category": "contact",
                "subject_type": "customer",
                "residency": "eu",
                "retention": "P30D",
            },
        },
    ):
        written = export(here / "consent_state.csv", here / "nightly.csv")

    print(f"exported {written} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
