"""Offline invented fixture proof only; does not contact netcup."""

from billharbor_sdk import DocumentKind
from billharbor_vendors.synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "netcup"
    transport = "browser"
    document_kinds = (DocumentKind.INVOICE,)
