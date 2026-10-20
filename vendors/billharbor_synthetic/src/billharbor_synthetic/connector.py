"""Offline reference connector exercising the existing neutral SDK."""
from billharbor_sdk import DocumentKind
from .synthetic import SyntheticConnector


class Connector(SyntheticConnector):
    connector_id = "billharbor_synthetic"
    transport = "api"
    document_kinds = (DocumentKind.INVOICE, DocumentKind.CREDIT_NOTE, DocumentKind.SETTLEMENT)


async def create_connector(options, resolver):
    """Construct the invented offline source from a verified optional fixture."""
    import hashlib
    from pathlib import Path

    unknown = set(options) - {"fixture_path", "fixture_sha256", "page_size"}
    if unknown:
        raise ValueError("Unsupported synthetic plugin options.")
    path = None
    if "fixture_path" in options:
        path = Path(options["fixture_path"])
        raw = path.read_bytes()
        if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != options.get("fixture_sha256"):
            raise ValueError("Fixture digest mismatch.")
    elif "fixture_sha256" in options:
        raise ValueError("Fixture digest requires a fixture path.")
    return Connector(path, page_size=options.get("page_size", 1))
