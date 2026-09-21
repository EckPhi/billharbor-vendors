"""Synthetic-only SDK proof; this module does not open a browser."""

from billharbor.sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "oekostrom_at"
    transport = "browser"
    document_kinds = (DocumentKind.INVOICE, DocumentKind.SETTLEMENT)
    supports_interaction = True
