"""Compatibility fixture helper; implementation belongs to the synthetic plugin."""
from billharbor_synthetic.synthetic import SyntheticConnector as _SyntheticConnector


class SyntheticConnector(_SyntheticConnector):
    fixture_package = "billharbor_vendors"

    def __init__(self, fixture_path=None, *, page_size=100):
        self.fixture_resource = f"data/fixtures/{self.connector_id}.json"
        super().__init__(fixture_path, page_size=page_size)
