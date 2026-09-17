"""Synthetic-only SDK proof; this module does not call Amazon."""

from billharbor.sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "amazon_business_de"
    transport = "api"
    document_kinds = (DocumentKind.INVOICE, DocumentKind.CREDIT_NOTE)
