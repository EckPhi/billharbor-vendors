"""Fixture-only connector used to prove SDK conformance without live access."""

from __future__ import annotations

import base64
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
        scope_by_id = {scope.id: scope for scope in scopes}
        offset = 0 if checkpoint_id is None else int(checkpoint_id.removeprefix("offset_"))
        records = [
            item for item in self._fixture["documents"]
            if item["scope_id"] in scope_by_id
            and starts_on <= date.fromisoformat(item["issue_date"]) <= ends_on
        ]
        page_records = records[offset : offset + self._page_size]
        documents = tuple(self._reference(scope_by_id[item["scope_id"]], item) for item in page_records)
        next_offset = offset + len(page_records)
        terminal = next_offset >= len(records)
        return DiscoveryPage(
            documents=documents,
            checkpoint_id=None if terminal else f"offset_{next_offset}",
            terminal=terminal,
        )

    async def fetch_document(
        self, context: ConnectorContext, reference: DocumentReference
    ) -> ArtifactPublication:
        self._ensure_ready(context)
        scope_ids = {scope.id for scope in reference.scopes}
        item = next((candidate for candidate in self._fixture["documents"]
                     if candidate["native_id"] == reference.source_document_id
                     and candidate["scope_id"] in scope_ids
                     and DocumentKind(candidate["document_kind"]) is reference.document_kind), None)
        if item is None:
            raise LookupError("synthetic document reference was not discovered")
        content = base64.b64decode(item["content_base64"], validate=True)
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
            source_document_id=item["native_id"], document_kind=DocumentKind(item["document_kind"]),
            observed_at=datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00")),
            scopes=(scope,), observations=observations,
        )

    def _ensure_ready(self, context: ConnectorContext) -> None:
        if self._closed:
            raise RuntimeError("connector is closed")
        if context.cancelled():
            raise RuntimeError("execution is cancelled")
