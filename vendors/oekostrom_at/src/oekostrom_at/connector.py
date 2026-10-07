"""Synthetic-only SDK proof; this module does not open a browser."""

from billharbor.sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "oekostrom_at"
    transport = "browser"
    document_kinds = (DocumentKind.INVOICE, DocumentKind.CREDIT_NOTE, DocumentKind.SETTLEMENT)
    supports_interaction = True


class LabelConnector(Connector):
    """Invented label fixtures only; preserves the legacy default connector."""

    fixture_version = "oekostrom-label-synthetic/1"

    @staticmethod
    def _source_id(item):
        from .identity import source_id
        return source_id(item["scope_kind"], item["scope_id"], item["document_kind"], item["designation"])
