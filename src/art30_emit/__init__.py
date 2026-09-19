"""Put the Art. 30 facet on the wire from code that emits nothing today.

dbt, Airflow, Spark and Flink all emit OpenLineage, and none of them emits
``purpose`` or ``legal_basis``. Everything else a record of processing activities
needs can be evidenced from what an organisation already runs; those two cannot,
which is why they end up asserted in a file beside the code and drift from it.

This puts them in the event, emitted by the thing that ran, for the code nobody
else instruments: a Lambda, a stored procedure behind a wrapper, a cron job, a
notebook that matters more than it should.

Two rules it keeps, and they are the reason it is worth having rather than a
snippet in a wiki:

**It emits the published facet, not one of its own.** The schema is
``openlineage-art30-processing-facet.json`` in cordata-tech/qedro, generated from
a governance model rather than written beside it. A second spelling of the same
two fields would be a private vocabulary wearing a standard's clothes.

**It never decides anything.** No validation against a compiled list of purposes,
no guessing a legal basis from a job name, no default that fills a field nobody
declared. What the caller says is what goes on the wire, and what the caller does
not say is absent — which is the state a record has to be able to report.
"""

from __future__ import annotations

from .emit import Declaration, declare, emit

__version__ = "0.1.0"

#: The key the facet occupies in ``job.facets``, and the published schema it
#: conforms to. Both are the same strings `pipeline-runtime` emits and `qedro`
#: reads; a change here breaks a contract somebody else's record depends on.
FACET_KEY = "processing"
FACET_SCHEMA = (
    "https://github.com/cordata-tech/qedro/blob/main/schemas/"
    "openlineage-art30-processing-facet.json"
)

__all__ = ["FACET_KEY", "FACET_SCHEMA", "Declaration", "__version__", "declare", "emit"]
