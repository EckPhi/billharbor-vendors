"""Offline invented fixture proof only; does not contact Lidl Connect Austria."""

from billharbor_sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "lidl_connect_at"
    transport = "browser"
    document_kinds = (DocumentKind.INVOICE,)
