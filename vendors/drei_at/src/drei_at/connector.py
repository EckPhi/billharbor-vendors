"""Offline invented fixture proof only; does not contact Drei Austria."""

from billharbor_sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "drei_at"
    transport = "browser"
    document_kinds = (DocumentKind.INVOICE,)
