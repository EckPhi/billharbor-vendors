"""Use sibling source trees until the independently released SDK is published."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BILLHARBOR = ROOT.parent / "billharbor"

for source in (
    BILLHARBOR / "src",
    ROOT / "src",
    ROOT / "vendors/amazon_business_de/src",
    ROOT / "vendors/oekostrom_at/src",
):
    sys.path.insert(0, str(source))

