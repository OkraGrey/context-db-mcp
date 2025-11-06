"""Unit tests for the Context DB MCP server."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from context_db_mcp.config import Settings
from context_db_mcp.server import build_server
from context_db_mcp.vector_store import (
    IngestDocumentRequest,
    IngestDocumentResponse,
    OpenAIContextStore,
    RetrieveRelevantChunksRequest,
    RetrieveRelevantChunksResponse,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    # Create settings without loading .env file
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-key",
        "CONTEXT_DB_VECTOR_STORE_NAME": "test-store",
        "CONTEXT_DB_DEFAULT_MAX_RESULTS": "5",
        "CONTEXT_DB_LOG_LEVEL": "DEBUG",
    }):
        settings = Settings(_env_file=None)
        return settings


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()
    
    # Mock vector store
    mock_store = Mock()
    mock_store.id = "vs_test123"
    mock_store.name = "test-store"
    
    # Mock vector store file
    mock_file = Mock()
    mock_file.id = "file_test123"
    mock_file.name = "test-document.txt"
    mock_file.status = "completed"
    mock_file.attributes = {"document_id": "doc1", "summary": "Test"}
    
    # Setup client methods
    client.vector_stores.retrieve.return_value = mock_store
    client.vector_stores.create.return_value = mock_store
    client.vector_stores.list.return_value = [mock_store]
    client.vector_stores.files.upload_and_poll.return_value = mock_file
    
    # Mock search results
    mock_search_result = Mock()
    mock_search_result.file_id = "file_test123"
    mock_search_result.filename = "test-document.txt"
    mock_search_result.score = 0.95
    mock_search_result.attributes = {"summary": "Test"}
    
    mock_content = Mock()
    mock_content.type = "text"
    mock_content.text = "This is test content"
    mock_search_result.content = [mock_content]
    
    client.vector_stores.search.return_value = [mock_search_result]
    
    return client


class TestSettings:
    """Test configuration management."""
    
    def test_settings_from_env(self):
        """Test that settings load from environment variables."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-key",
            "CONTEXT_DB_VECTOR_STORE_NAME": "my-store",
            "CONTEXT_DB_LOG_LEVEL": "DEBUG",
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.openai_api_key == "sk-test-key"
            assert settings.default_vector_store_name == "my-store"
            assert settings.log_level == "DEBUG"
    
    def test_settings_defaults(self, mock_settings):
        """Test default settings values."""
        assert mock_settings.default_max_results == 5
        assert mock_settings.request_timeout_seconds == 120.0
        assert mock_settings.log_level == "DEBUG"


class TestIngestDocumentRequest:
    """Test document ingestion request validation."""
    
    def test_valid_request(self):
        """Test valid ingestion request."""
        request = IngestDocumentRequest(
            content="This is test content",
            document_id="doc1",
            summary="Test document",
        )
        assert request.content == "This is test content"
        assert request.document_id == "doc1"
        assert request.summary == "Test document"
    
    def test_empty_content_raises_error(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValueError, match="empty after stripping whitespace"):
            IngestDocumentRequest(content="   ")
    
    def test_whitespace_trimmed(self):
        """Test content with whitespace is valid."""
        request = IngestDocumentRequest(content="  test content  ")
        assert request.content == "  test content  "


class TestRetrieveRelevantChunksRequest:
    """Test chunk retrieval request validation."""
    
    def test_valid_request(self):
        """Test valid retrieval request."""
        request = RetrieveRelevantChunksRequest(
            query="Find information about authentication",
            max_results=10,
            score_threshold=0.7,
        )
        assert request.query == "Find information about authentication"
        assert request.max_results == 10
        assert request.score_threshold == 0.7
    
    def test_empty_query_raises_error(self):
        """Test that empty query raises validation error."""
        with pytest.raises(ValueError, match="empty after stripping whitespace"):
            RetrieveRelevantChunksRequest(query="   ")
    
    def test_max_results_bounds(self):
        """Test max_results validation bounds."""
        # Valid ranges
        RetrieveRelevantChunksRequest(query="test", max_results=1)
        RetrieveRelevantChunksRequest(query="test", max_results=50)
        
        # Invalid ranges
        with pytest.raises(ValueError):
            RetrieveRelevantChunksRequest(query="test", max_results=0)
        
        with pytest.raises(ValueError):
            RetrieveRelevantChunksRequest(query="test", max_results=51)


class TestOpenAIContextStore:
    """Test vector store operations."""
    
    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                OpenAIContextStore(settings)
    
    @patch("context_db_mcp.vector_store.OpenAI")
    def test_init_with_api_key(self, mock_openai_class, mock_settings):
        """Test successful initialization with API key."""
        store = OpenAIContextStore(mock_settings)
        mock_openai_class.assert_called_once()
        assert store is not None
    
    @patch("context_db_mcp.vector_store.OpenAI")
    def test_ingest_document(self, mock_openai_class, mock_settings, mock_openai_client):
        """Test document ingestion."""
        mock_openai_class.return_value = mock_openai_client
        store = OpenAIContextStore(mock_settings)
        
        request = IngestDocumentRequest(
            content="Test document content",
            document_id="doc1",
            summary="Test Summary",
            filename="test.txt",
        )
        
        response = store.ingest(request)
        
        assert isinstance(response, IngestDocumentResponse)
        assert response.vector_store_id == "vs_test123"
        assert response.file_id == "file_test123"
        assert response.status == "completed"
        
        # Verify upload was called
        mock_openai_client.vector_stores.files.upload_and_poll.assert_called_once()
    
    @patch("context_db_mcp.vector_store.OpenAI")
    def test_retrieve_chunks(self, mock_openai_class, mock_settings, mock_openai_client):
        """Test chunk retrieval."""
        mock_openai_class.return_value = mock_openai_client
        store = OpenAIContextStore(mock_settings)
        
        request = RetrieveRelevantChunksRequest(
            query="Find authentication info",
            max_results=5,
        )
        
        response = store.retrieve(request)
        
        assert isinstance(response, RetrieveRelevantChunksResponse)
        assert response.vector_store_id == "vs_test123"
        assert response.query == "Find authentication info"
        assert len(response.results) > 0
        assert response.results[0].score == 0.95
        assert response.results[0].text == "This is test content"
        
        # Verify search was called
        mock_openai_client.vector_stores.search.assert_called_once()
    
    @patch("context_db_mcp.vector_store.OpenAI")
    def test_retrieve_with_score_threshold(self, mock_openai_class, mock_settings, mock_openai_client):
        """Test retrieval with score threshold filtering."""
        mock_openai_class.return_value = mock_openai_client
        
        # Setup multiple results with different scores
        result1 = Mock()
        result1.file_id = "file1"
        result1.filename = "doc1.txt"
        result1.score = 0.95
        result1.attributes = {}
        content1 = Mock()
        content1.type = "text"
        content1.text = "High score content"
        result1.content = [content1]
        
        result2 = Mock()
        result2.file_id = "file2"
        result2.filename = "doc2.txt"
        result2.score = 0.60
        result2.attributes = {}
        content2 = Mock()
        content2.type = "text"
        content2.text = "Low score content"
        result2.content = [content2]
        
        mock_openai_client.vector_stores.search.return_value = [result1, result2]
        
        store = OpenAIContextStore(mock_settings)
        
        request = RetrieveRelevantChunksRequest(
            query="test query",
            score_threshold=0.8,
        )
        
        response = store.retrieve(request)
        
        # Only high-score result should be returned
        assert len(response.results) == 1
        assert response.results[0].score == 0.95


class TestMCPServer:
    """Test MCP server setup and tools."""
    
    def test_build_server_with_settings(self, mock_settings):
        """Test server builds successfully with settings."""
        with patch("context_db_mcp.server.OpenAIContextStore"):
            with patch("context_db_mcp.server.FastMCP") as mock_fastmcp:
                mock_server = Mock()
                mock_server.name = "context-db-mcp"
                mock_fastmcp.return_value = mock_server
                
                server = build_server(mock_settings)
                
                assert server is not None
                assert server.name == "context-db-mcp"
                mock_fastmcp.assert_called_once()
    
    def test_build_server_without_settings(self):
        """Test server builds with default settings from environment."""
        with patch("context_db_mcp.server.OpenAIContextStore"):
            with patch("context_db_mcp.server.FastMCP") as mock_fastmcp:
                with patch("context_db_mcp.config.Settings") as mock_settings_class:
                    mock_settings_class.return_value = Mock(
                        openai_api_key="sk-test-key",
                        default_vector_store_name="test-store",
                        log_level="INFO",
                    )
                    mock_server = Mock()
                    mock_fastmcp.return_value = mock_server
                    
                    server = build_server()
                    
                    assert server is not None
                    mock_fastmcp.assert_called_once()

