"""Exact portal designation identity; account scoping is engine-owned."""
import hashlib
import json

POLICY = "oekostrom-label/1"


def source_id(scope_kind: str, scope_id: str, kind: str, designation: str) -> str:
    if not isinstance(designation, str) or not designation.strip() or len(designation) > 2000:
        raise ValueError("Missing or invalid exact Bezeichnung identity")
    if not all(isinstance(value, str) and value for value in (scope_kind, scope_id, kind)):
        raise ValueError("Missing identity scope or kind")
    parts = [POLICY, scope_kind, scope_id, kind, designation]
    encoded = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "oekostrom_label_v1_" + hashlib.sha256(encoded).hexdigest()
