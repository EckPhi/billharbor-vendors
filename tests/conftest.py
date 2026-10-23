"""Use sibling source trees until the independently released SDK is published."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BILLHARBOR = ROOT.parent / "billharbor"

for source in (
    # Engine is test-only for cross-boundary outbox integration, never a runtime dependency.
    BILLHARBOR / "src",
    BILLHARBOR / "packages/connector-sdk/src",
    ROOT / "src",
    ROOT / "vendors/drei_at/src",
    ROOT / "vendors/lidl_connect_at/src",
    ROOT / "vendors/netcup/src",
    ROOT / "vendors/hornbach_at/src",
    ROOT / "vendors/billharbor_synthetic/src",
    ROOT / "vendors/amazon_business_de/src",
    ROOT / "vendors/oekostrom_at/src",
):
    sys.path.insert(0, str(source))

