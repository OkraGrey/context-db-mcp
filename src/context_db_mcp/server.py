"""Entry point for the Context DB MCP server."""

from __future__ import annotations

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context

from . import __version__
from .config import Settings, get_settings
from .vector_store import (
    GetVectorStoreInfoResponse,
    IngestDocumentRequest,
    IngestDocumentResponse,
    OpenAIContextStore,
    RetrieveRelevantChunksRequest,
    RetrieveRelevantChunksResponse,
)


LOGGER_NAME = "context_db_mcp"


def configure_logging(log_level: str) -> None:
    """Configure root logging based on user preference."""

    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_server(settings: Optional[Settings] = None) -> FastMCP:
    """Instantiate the MCP server and register tooling."""

    if settings is None:
        settings = get_settings()

    configure_logging(settings.log_level)
    logger = logging.getLogger(LOGGER_NAME)

    store = OpenAIContextStore(settings)

    server = FastMCP(
        "context-db-mcp",
        instructions=(
            "Upload change summaries to an OpenAI vector store and fetch the most relevant "
            "context snippets on demand."
        ),
    )

    @server.tool(
        name="ingest_document",
        title="Ingest Document",
        description=(
            "Add a plain-text document or feature summary into the configured OpenAI vector store "
            "so that future tasks can retrieve it.\n\n"
            "Required Parameters:\n"
            "- content (string): The plain-text content to ingest. Must not be empty.\n\n"
            "Optional Parameters:\n"
            "- vector_store_id (string): Target vector store ID. If omitted, uses default from config.\n"
            "- vector_store_name (string): Vector store name to create/find. Used only if vector_store_id is not provided.\n"
            "- document_id (string): Stable identifier for the document (stored as file attribute).\n"
            "- filename (string): Logical filename for the uploaded document. Auto-generated if omitted.\n"
            "- summary (string): High-level summary or title (stored as attribute).\n"
            "- attributes (object): Additional key/value pairs to attach as file attributes.\n"
            "- chunking_strategy (object): OpenAI chunking strategy configuration.\n"
            "- mime_type (string): MIME type of the file. Defaults to 'text/plain'.\n\n"
            "Example:\n"
            "{\n"
            "  \"content\": \"This is my document content\",\n"
            "  \"document_id\": \"doc-2025-11-06\",\n"
            "  \"summary\": \"Summary of feature implementation\",\n"
            "  \"filename\": \"feature-summary.txt\"\n"
            "}"
        ),
        structured_output=True,
    )
    def ingest_document(request: IngestDocumentRequest, ctx: Context) -> IngestDocumentResponse:
        """Tool for ingesting documents into the vector store."""

        ctx.info("Ingesting document into vector store...")
        result = store.ingest(request)
        ctx.info(
            f"Stored file {result.file_id} in vector store {result.vector_store_id} with status {result.status}"
        )
        logger.debug("Attributes applied to file %s: %s", result.file_id, result.attributes)
        return result

    @server.tool(
        name="retrieve_relevant_chunks",
        title="Retrieve Relevant Chunks",
        description=(
            "Search the configured OpenAI vector store for the chunks most relevant to the provided query.\n\n"
            "Required Parameters:\n"
            "- query (string): The search query that drives similarity search. Must not be empty.\n\n"
            "Optional Parameters:\n"
            "- vector_store_id (string): Vector store to query. If omitted, uses default from config.\n"
            "- max_results (integer): Maximum number of chunks to return. Range: 1-50. Uses default from config if omitted.\n"
            "- score_threshold (float): Minimum similarity score (0.0-1.0) required for chunk inclusion. Lower scores = less similar.\n"
            "- attributes_filter (object): Exact-match filters on file attributes (e.g., {\"document_id\": \"doc-123\"}).\n"
            "- rewrite_query (boolean): Enable/disable OpenAI's automatic query rewriting for better results.\n\n"
            "Response Format:\n"
            "Returns a list of chunks, each containing:\n"
            "- file_id: The vector store file ID\n"
            "- filename: Name of the source file\n"
            "- score: Similarity score (0.0-1.0, higher = more relevant)\n"
            "- text: The actual chunk content\n"
            "- attributes: File metadata (document_id, summary, ingested_at, etc.)\n\n"
            "Example:\n"
            "{\n"
            "  \"query\": \"How does user authentication work?\",\n"
            "  \"max_results\": 5,\n"
            "  \"score_threshold\": 0.7\n"
            "}"
        ),
        structured_output=True,
    )
    def retrieve_relevant_chunks(
        request: RetrieveRelevantChunksRequest, ctx: Context
    ) -> RetrieveRelevantChunksResponse:
        """Tool for retrieving relevant chunks from the vector store."""

        ctx.info("Retrieving relevant chunks from vector store...")
        result = store.retrieve(request)
        ctx.info(
            f"Found {len(result.results)} relevant chunks from vector store {result.vector_store_id}"
        )
        return result

    @server.tool(
        name="get_vector_store_info",
        title="Get Vector Store Info",
        description=(
            "Get information about the configured OpenAI vector store.\n\n"
            "Optional Parameters:\n"
            "- vector_store_id (string): Vector store ID to query. If omitted, uses default from config.\n\n"
            "Response Format:\n"
            "Returns information about the vector store:\n"
            "- vector_store_id: The ID of the vector store\n"
            "- vector_store_name: The name of the vector store (if available)\n\n"
            "Example:\n"
            "{\n"
            "  \"vector_store_id\": \"vs_abc123\"\n"
            "}"
        ),
        structured_output=True,
    )
    def get_vector_store_info(
        vector_store_id: Optional[str] = None, ctx: Context = None
    ) -> GetVectorStoreInfoResponse:
        """Tool for getting vector store information."""

        if ctx:
            ctx.info("Retrieving vector store information...")
        result = store.get_vector_store_info(vector_store_id)
        if ctx:
            ctx.info(
                f"Vector store ID: {result.vector_store_id}, Name: {result.vector_store_name or 'N/A'}"
            )
        return result

    return server


def main() -> None:
    """Start the MCP server using stdio transport."""

    server = build_server()
    server.run()


if __name__ == "__main__":
    main()




