"""Fixture-only connector used to prove SDK conformance without live access."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import date, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping

from billharbor.sdk import (
    ArtifactPublication, ConnectorCapabilities, DiscoveryPage,
    DocumentKind, DocumentReference, Observation, ObservationField,
    ObservationSource, ObservationValueType, Scope, ScopeKind, SessionState,
)
from billharbor.sdk.v2 import ConnectorContext


class SyntheticConnector:
    """Read invented records from disk; deliberately has no network transport."""

    connector_id: str
    transport: str
    document_kinds: tuple[DocumentKind, ...]
    supports_interaction: bool = False

    def __init__(self, fixture_path: Path | None = None, *, page_size: int = 100) -> None:
        fixture = fixture_path or files("billharbor_vendors").joinpath(
            "data", "fixtures", f"{self.connector_id}.json"
        )
        with fixture.open(encoding="utf-8") as handle:
            self._fixture: dict[str, Any] = json.load(handle)
        if self._fixture.get("synthetic") is not True:
            raise ValueError("connector accepts only explicitly synthetic fixture data")
        if self._fixture.get("connector_id") != self.connector_id:
            raise ValueError("fixture connector_id does not match connector")
        if self._fixture.get("fixture_version") != "vendor-synthetic/1":
            raise ValueError("unsupported synthetic fixture version")
        known_scopes = {(item["kind"], item["id"]) for item in self._fixture["scopes"]}
        if len(known_scopes) != len(self._fixture["scopes"]):
            raise ValueError("duplicate synthetic scope")
        identities = set()
        for item in self._fixture["documents"]:
            identity = (item["scope_kind"], item["scope_id"], item["document_kind"], item["native_id"])
            if (item["scope_kind"], item["scope_id"]) not in known_scopes or identity in identities:
                raise ValueError("invalid or duplicate synthetic document scope identity")
            identities.add(identity)
            if DocumentKind(item["document_kind"]) not in self.document_kinds:
                raise ValueError("unsupported synthetic document kind")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")
        self._page_size = page_size
        self._closed = False

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            connector_id=self.connector_id,
            transports=(self.transport,),
            document_kinds=self.document_kinds,
            supports_interaction=self.supports_interaction,
        )

    async def check_session(self, context: ConnectorContext) -> SessionState:
        self._ensure_ready(context)
        return SessionState.READY

    async def list_scopes(self, context: ConnectorContext) -> tuple[Scope, ...]:
        self._ensure_ready(context)
        return tuple(Scope(kind=ScopeKind(item["kind"]), id=item["id"]) for item in self._fixture["scopes"])

    async def discover_page(
        self, context: ConnectorContext, *, starts_on: date, ends_on: date,
        scopes: tuple[Scope, ...], checkpoint_id: str | None,
    ) -> DiscoveryPage:
        self._ensure_ready(context)
        if not scopes:
            raise ValueError("at least one explicit scope is required")
        available = {(scope.kind, scope.id) for scope in await self.list_scopes(context)}
        if len(set(scopes)) != len(scopes) or not {(scope.kind, scope.id) for scope in scopes} <= available:
            raise ValueError("unknown synthetic scope")
        scope_by_identity = {(scope.kind.value, scope.id): scope for scope in scopes}
        query = {
            "starts_on": starts_on.isoformat(),
            "ends_on": ends_on.isoformat(),
            "scopes": sorted((scope.kind.value, scope.id) for scope in scopes),
        }
        query_digest = hashlib.sha256(
            json.dumps(query, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]
        if checkpoint_id is None:
            offset = 0
        elif checkpoint_id.startswith("offset_"):
            # Compatibility for interrupted 0.3 synthetic executions. New
            # checkpoints are always query-bound.
            try:
                offset = int(checkpoint_id.removeprefix("offset_"))
            except ValueError as exc:
                raise ValueError("checkpoint is invalid") from exc
            if offset < 0:
                raise ValueError("checkpoint is invalid")
        else:
            prefix = f"cursor_{query_digest}_"
            if not checkpoint_id.startswith(prefix):
                raise ValueError("checkpoint does not match discovery filters")
            try:
                offset = int(checkpoint_id.removeprefix(prefix))
            except ValueError as exc:
                raise ValueError("checkpoint is invalid") from exc
            if offset < 0:
                raise ValueError("checkpoint is invalid")
        records = [
            item for item in self._fixture["documents"]
            if (item["scope_kind"], item["scope_id"]) in scope_by_identity
            and starts_on <= date.fromisoformat(item["issue_date"]) <= ends_on
        ]
        if checkpoint_id is not None and (
            offset <= 0 or offset >= len(records) or offset % self._page_size != 0
        ):
            raise ValueError("checkpoint offset was not emitted for this result set")
        page_records = records[offset : offset + self._page_size]
        documents = tuple(self._reference(scope_by_identity[(item["scope_kind"], item["scope_id"])], item) for item in page_records)
        next_offset = offset + len(page_records)
        terminal = next_offset >= len(records)
        return DiscoveryPage(
            documents=documents,
            checkpoint_id=None if terminal else f"cursor_{query_digest}_{next_offset}",
            terminal=terminal,
        )

    async def fetch_document(
        self, context: ConnectorContext, reference: DocumentReference
    ) -> ArtifactPublication:
        self._ensure_ready(context)
        scope_ids = {(scope.kind.value, scope.id) for scope in reference.scopes}
        item = next((candidate for candidate in self._fixture["documents"]
                     if self._source_id(candidate) == reference.source_document_id
                     and (candidate["scope_kind"], candidate["scope_id"]) in scope_ids
                     and DocumentKind(candidate["document_kind"]) is reference.document_kind), None)
        if item is None:
            raise LookupError("synthetic document reference was not discovered")
        content = base64.b64decode(item["content_base64"], validate=True)
        if not content.startswith(b"%PDF-") or item["media_type"] != "application/pdf":
            raise ValueError("synthetic original is not a PDF")
        return await context.publish_artifact(
            artifact_id=f"fixture_{reference.source_document_id}",
            filename=item["filename"], media_type=item["media_type"],
            content=content,
        )

    async def close(self) -> None:
        self._closed = True

    def _reference(self, scope: Scope, item: Mapping[str, Any]) -> DocumentReference:
        observations = tuple(Observation(
            field=ObservationField(value["field"]),
            value_type=ObservationValueType(value["value_type"]),
            value=value["value"], source=ObservationSource(value["source"]),
            source_path=value["source_path"],
        ) for value in item["observations"])
        return DocumentReference(
            source_document_id=self._source_id(item), document_kind=DocumentKind(item["document_kind"]),
            observed_at=datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00")),
            scopes=(scope,), observations=observations,
        )

    def _ensure_ready(self, context: ConnectorContext) -> None:
        if self._closed:
            raise RuntimeError("connector is closed")
        if context.cancelled():
            raise RuntimeError("execution is cancelled")

    @staticmethod
    def _source_id(item: Mapping[str, Any]) -> str:
        parts = (item["scope_kind"], item["scope_id"], item["document_kind"], item["native_id"])
        return "synthetic_" + hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()
