"""Offline reference connector exercising the existing neutral SDK."""
from billharbor.sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "billharbor_synthetic"
    transport = "api"
    document_kinds = (DocumentKind.INVOICE, DocumentKind.CREDIT_NOTE, DocumentKind.SETTLEMENT)
