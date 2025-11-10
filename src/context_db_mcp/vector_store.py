"""Abstractions for interacting with the OpenAI vector store API."""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Union

from openai import OpenAI
from openai._types import FileTypes
from openai.types import VectorStore
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import Settings


logger = logging.getLogger(__name__)


AttributesType = Dict[str, Union[str, float, bool]]


class IngestDocumentRequest(BaseModel):
    """Schema for ingesting a document into a vector store."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., description="Plain-text content to add to the vector store.")
    vector_store_id: Optional[str] = Field(
        default=None,
        description="Target vector store ID. Falls back to defaults when omitted.",
    )
    vector_store_name: Optional[str] = Field(
        default=None,
        description="Optional vector store name to create when an ID is not provided.",
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Stable identifier for the ingested document (stored as file attribute).",
    )
    filename: Optional[str] = Field(
        default=None,
        description="Logical filename used when uploading the document.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="High-level summary or title for the document (stored as attribute).",
    )
    attributes: Optional[AttributesType] = Field(
        default=None,
        description="Additional attribute key/value pairs to attach to the vector store file.",
    )
    chunking_strategy: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional chunking strategy forwarded to the OpenAI API.",
    )
    mime_type: str = Field(
        default="text/plain",
        description="MIME type flagged on the uploaded file.",
    )

    @model_validator(mode="after")
    def ensure_store_reference(self) -> "IngestDocumentRequest":
        if not self.content.strip():
            raise ValueError("The document content is empty after stripping whitespace.")
        return self


class IngestDocumentResponse(BaseModel):
    """Structured result returned after ingesting a document."""

    model_config = ConfigDict(extra="forbid")

    vector_store_id: str
    vector_store_name: Optional[str]
    file_id: str
    filename: str
    status: str
    attributes: Optional[AttributesType]


class RetrieveRelevantChunksRequest(BaseModel):
    """Schema for retrieving context from a vector store."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="User query that drives similarity search.")
    vector_store_id: Optional[str] = Field(
        default=None,
        description="Vector store to query. Falls back to defaults when omitted.",
    )
    max_results: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Maximum number of chunks to return.",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        description="Minimum similarity score required for inclusion.",
    )
    attributes_filter: Optional[AttributesType] = Field(
        default=None,
        description="Exact-match attribute filters applied during vector store search.",
    )
    rewrite_query: Optional[bool] = Field(
        default=None,
        description="Toggle OpenAI query rewriting.",
    )

    @model_validator(mode="after")
    def ensure_query(self) -> "RetrieveRelevantChunksRequest":
        if not self.query.strip():
            raise ValueError("The search query is empty after stripping whitespace.")
        return self


class RetrievedChunk(BaseModel):
    """Chunk result emitted by a retrieval call."""

    model_config = ConfigDict(extra="forbid")

    file_id: str
    filename: str
    score: float
    text: str
    attributes: Optional[AttributesType]


class RetrieveRelevantChunksResponse(BaseModel):
    """Structured response body for chunk retrieval."""

    model_config = ConfigDict(extra="forbid")

    vector_store_id: str
    query: str
    results: List[RetrievedChunk]


class GetVectorStoreInfoResponse(BaseModel):
    """Response containing vector store information."""

    model_config = ConfigDict(extra="forbid")

    vector_store_id: str
    vector_store_name: Optional[str]


class OpenAIContextStore:
    """Helper class that wraps the OpenAI SDK for vector store operations."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY (or CONTEXT_DB_OPENAI_API_KEY) must be set before starting the MCP server."
            )

        self._settings = settings
        self._client = OpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization,
            project=settings.openai_project,
            timeout=settings.request_timeout_seconds,
            max_retries=3,
        )

    def ensure_vector_store(
        self,
        vector_store_id: Optional[str],
        vector_store_name: Optional[str],
        metadata: Optional[AttributesType] = None,
    ) -> VectorStore:
        """Resolve or lazily create a vector store."""

        if vector_store_id:
            logger.debug("Using provided vector store id %s", vector_store_id)
            return self._client.vector_stores.retrieve(vector_store_id)

        if not vector_store_name:
            fallback_id = self._settings.default_vector_store_id
            if fallback_id:
                logger.debug("Falling back to configured vector store id %s", fallback_id)
                return self._client.vector_stores.retrieve(fallback_id)

            fallback_name = self._settings.default_vector_store_name
            if fallback_name:
                logger.debug("Attempting to locate default vector store named %s", fallback_name)
                existing = self._find_vector_store_by_name(fallback_name)
                if existing:
                    return existing
                logger.info("Creating default vector store named %s", fallback_name)
                return self._client.vector_stores.create(name=fallback_name, metadata=metadata)

            raise ValueError(
                "No vector store identifier was provided and no defaults are configured."
            )

        logger.debug("Attempting to locate vector store named %s", vector_store_name)
        existing_store = self._find_vector_store_by_name(vector_store_name)
        if existing_store:
            return existing_store

        logger.info("Creating vector store named %s", vector_store_name)
        return self._client.vector_stores.create(name=vector_store_name, metadata=metadata)

    def _prepare_upload(
        self,
        filename: str,
        content: str,
        mime_type: str,
    ) -> FileTypes:
        buffer = io.BytesIO(content.encode("utf-8"))
        buffer.seek(0)
        return (filename, buffer, mime_type)

    def ingest(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        """Upload a document into the configured vector store."""

        metadata: AttributesType | None = None
        if request.vector_store_name:
            metadata = {}

        vector_store = self.ensure_vector_store(
            vector_store_id=request.vector_store_id,
            vector_store_name=request.vector_store_name,
            metadata=metadata,
        )

        filename = request.filename or self._derive_filename(request)
        attributes = dict(request.attributes or {})
        if request.document_id:
            attributes.setdefault("document_id", request.document_id)
        if request.summary:
            attributes.setdefault("summary", request.summary)
        attributes.setdefault("ingested_at", datetime.now(timezone.utc).isoformat())

        upload = self._prepare_upload(filename, request.content, request.mime_type)

        upload_kwargs: Dict[str, Any] = {}
        if request.chunking_strategy is not None:
            upload_kwargs["chunking_strategy"] = request.chunking_strategy

        logger.info(
            "Uploading document %s to vector store %s", filename, vector_store.id
        )

        vector_store_file = self._client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=upload,
            attributes=attributes or None,
            **upload_kwargs,
        )

        if vector_store_file.status != "completed":
            logger.warning(
                "Vector store file %s completed with status %s", vector_store_file.id, vector_store_file.status
            )

        return IngestDocumentResponse(
            vector_store_id=vector_store.id,
            vector_store_name=getattr(vector_store, "name", None),
            file_id=vector_store_file.id,
            filename=filename,  # Use the filename we prepared, not from vector_store_file
            status=vector_store_file.status,
            attributes=vector_store_file.attributes,
        )

    def retrieve(self, request: RetrieveRelevantChunksRequest) -> RetrieveRelevantChunksResponse:
        """Retrieve relevant chunks from the vector store."""

        vector_store = self.ensure_vector_store(
            vector_store_id=request.vector_store_id,
            vector_store_name=None,
        )

        max_results = request.max_results or self._settings.default_max_results
        search_kwargs: Dict[str, Any] = {
            "query": request.query,
            "max_num_results": max_results,
        }
        if request.attributes_filter:
            search_kwargs["filters"] = {"attributes": request.attributes_filter}
        if request.rewrite_query is not None:
            search_kwargs["rewrite_query"] = request.rewrite_query

        logger.debug(
            "Searching vector store %s for query %s", vector_store.id, request.query
        )

        search_results = self._client.vector_stores.search(
            vector_store.id, **search_kwargs
        )

        collected: List[RetrievedChunk] = []
        for result in search_results:
            if request.score_threshold is not None and result.score < request.score_threshold:
                continue
            text = "\n\n".join(chunk.text for chunk in result.content if chunk.type == "text")
            collected.append(
                RetrievedChunk(
                    file_id=result.file_id,
                    filename=result.filename,
                    score=result.score,
                    text=text,
                    attributes=result.attributes,
                )
            )

        return RetrieveRelevantChunksResponse(
            vector_store_id=vector_store.id,
            query=request.query,
            results=collected,
        )

    def get_vector_store_info(
        self, vector_store_id: Optional[str] = None
    ) -> GetVectorStoreInfoResponse:
        """Get information about the configured vector store."""

        vector_store = self.ensure_vector_store(
            vector_store_id=vector_store_id,
            vector_store_name=None,
        )

        return GetVectorStoreInfoResponse(
            vector_store_id=vector_store.id,
            vector_store_name=getattr(vector_store, "name", None),
        )

    def _find_vector_store_by_name(self, name: str) -> Optional[VectorStore]:
        """Return an existing vector store that matches the provided name."""

        try:
            pages = self._client.vector_stores.list(limit=100, order="desc")
        except Exception as exc:  # pragma: no cover - defensive guard for API errors
            logger.warning("Failed to list vector stores: %s", exc)
            return None

        for store in pages:
            if getattr(store, "name", None) == name:
                return store

        return None

    @staticmethod
    def _derive_filename(request: IngestDocumentRequest) -> str:
        if request.document_id:
            return f"{request.document_id}.txt"
        if request.summary:
            slug = request.summary.lower().replace(" ", "-")[:40]
            return f"{slug or 'context'}-{int(datetime.now(timezone.utc).timestamp())}.txt"
        return f"context-{int(datetime.now(timezone.utc).timestamp())}.txt"


__all__ = [
    "AttributesType",
    "IngestDocumentRequest",
    "IngestDocumentResponse",
    "RetrieveRelevantChunksRequest",
    "RetrieveRelevantChunksResponse",
    "RetrievedChunk",
    "GetVectorStoreInfoResponse",
    "OpenAIContextStore",
]

