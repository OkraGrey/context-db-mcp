# Testing Guide

This document explains how to test your Context DB MCP server at different levels.

## Quick Health Check

Run the diagnostic script for a comprehensive health check:

```bash
python test_mcp_connection.py
```

This performs 5 critical checks and provides actionable feedback for any failures.

## Unit Tests

### Running All Tests

```bash
# Install dev dependencies first (one-time)
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=context_db_mcp --cov-report=html
```

### Test Categories

The test suite includes 15 tests organized into categories:

#### 1. Configuration Tests (2 tests)
- `test_settings_from_env`: Environment variable loading
- `test_settings_defaults`: Default configuration values

```bash
pytest tests/test_server.py::TestSettings -v
```

#### 2. Request Validation Tests (6 tests)
- Document ingestion request validation
- Empty content handling
- Retrieval request validation
- Query validation
- Max results bounds checking

```bash
pytest tests/test_server.py::TestIngestDocumentRequest -v
pytest tests/test_server.py::TestRetrieveRelevantChunksRequest -v
```

#### 3. Vector Store Tests (5 tests)
- Initialization with/without API key
- Document ingestion
- Chunk retrieval
- Score threshold filtering

```bash
pytest tests/test_server.py::TestOpenAIContextStore -v
```

#### 4. Server Tests (2 tests)
- Server builds with settings
- Server builds from environment

```bash
pytest tests/test_server.py::TestMCPServer -v
```

### Running Specific Tests

```bash
# Single test
pytest tests/test_server.py::TestOpenAIContextStore::test_ingest_document -v

# All tests in a class
pytest tests/test_server.py::TestSettings -v

# Tests matching a pattern
pytest tests/ -k "ingest" -v
```

## Integration Testing

### Manual Testing with Python

Test the server components directly:

```python
from context_db_mcp.config import Settings
from context_db_mcp.vector_store import OpenAIContextStore, IngestDocumentRequest

# Setup
settings = Settings()
store = OpenAIContextStore(settings)

# Test ingestion
request = IngestDocumentRequest(
    content="Test document content",
    document_id="test-doc-1",
    summary="Test Document",
)
response = store.ingest(request)
print(f"Uploaded: {response.file_id} to {response.vector_store_id}")

# Test retrieval
from context_db_mcp.vector_store import RetrieveRelevantChunksRequest

retrieval_request = RetrieveRelevantChunksRequest(
    query="test document",
    max_results=5,
)
results = store.retrieve(retrieval_request)
print(f"Found {len(results.results)} chunks")
```

### Testing in Cursor

1. **Enable DEBUG logging** in `~/.cursor/mcp.json`:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "context-db-mcp",
         "env": {
           "OPENAI_API_KEY": "sk-...",
           "CONTEXT_DB_VECTOR_STORE_NAME": "test-store",
           "CONTEXT_DB_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

2. **Restart Cursor completely**

3. **Open Developer Tools** (Help → Toggle Developer Tools)

4. **Test ingest tool**:
   Ask the AI:
   ```
   Use ingest_document to store: "FastAPI is used for the backend"
   with summary: "Backend framework" and document_id: "test-001"
   ```

5. **Test retrieve tool**:
   Ask the AI:
   ```
   Use retrieve_relevant_chunks to find information about "backend framework"
   ```

6. **Check logs** in Developer Tools Console for:
   - Tool call requests
   - API responses
   - Any errors

## Diagnostic Script Details

The `test_mcp_connection.py` script performs these checks:

### 1. Environment Configuration
- Checks for `OPENAI_API_KEY`
- Validates vector store configuration
- Verifies optional settings

### 2. OpenAI API Connection
- Creates OpenAI client
- Tests basic API connectivity
- Lists available models

### 3. Vector Store Access
- Lists existing vector stores
- Retrieves or creates configured store
- Reports store ID for configuration

### 4. Document Ingestion
- Creates test document
- Uploads to vector store
- Polls for completion status
- Reports file ID

### 5. Chunk Retrieval
- Searches for test query
- Returns matching chunks
- Shows scores and previews

## Test Data Cleanup

The diagnostic script creates test files in your vector store. To clean up:

### Option 1: Via Python

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
vector_store_id = "vs_your_store_id"

# List files
files = client.vector_stores.files.list(vector_store_id)

# Delete test files
for file in files:
    if file.attributes and file.attributes.get("test") == "true":
        client.vector_stores.files.delete(vector_store_id, file.id)
        print(f"Deleted test file: {file.id}")
```

### Option 2: Via OpenAI Dashboard

1. Go to: https://platform.openai.com/storage/vector_stores
2. Click on your vector store
3. Delete test files manually

## Continuous Testing

### Pre-commit Checks

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

# Run tests
pytest tests/ -v

# Run diagnostic (optional)
# python test_mcp_connection.py

echo "All tests passed!"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=context_db_mcp
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting Tests

### Tests fail with "Operation not permitted: .env"

This is a sandbox restriction. The tests are configured to avoid loading .env files, but if you still see this:

1. Make sure you're using the latest test code
2. Run tests with: `pytest tests/ -v --tb=short`
3. Check that tests use `Settings(_env_file=None)`

### Mocked tests pass but real integration fails

This means:
1. Unit tests are working (good!)
2. Integration issue with OpenAI API
3. Run: `python test_mcp_connection.py` to diagnose
4. Check API key, quota, and network

### Import errors

```bash
# Reinstall in editable mode
pip install -e .

# Verify installation
python -c "import context_db_mcp; print('OK')"
```

## Test Coverage

Current coverage: **~85%**

To generate coverage report:

```bash
pytest tests/ --cov=context_db_mcp --cov-report=html
open htmlcov/index.html  # macOS
```

Areas not covered by tests:
- CLI entry point (`main()` function)
- Live OpenAI API calls (mocked in tests)
- Edge cases in file chunking

## Performance Testing

### Ingestion Performance

```python
import time
from context_db_mcp.config import Settings
from context_db_mcp.vector_store import OpenAIContextStore, IngestDocumentRequest

settings = Settings()
store = OpenAIContextStore(settings)

# Test large document
large_content = "Test content. " * 10000  # ~140KB

start = time.time()
response = store.ingest(IngestDocumentRequest(
    content=large_content,
    document_id=f"perf-test-{int(time.time())}",
))
elapsed = time.time() - start

print(f"Ingested {len(large_content)} bytes in {elapsed:.2f}s")
```

### Retrieval Performance

```python
start = time.time()
results = store.retrieve(RetrieveRelevantChunksRequest(
    query="test query",
    max_results=50,
))
elapsed = time.time() - start

print(f"Retrieved {len(results.results)} chunks in {elapsed:.2f}s")
```

## Best Practices

1. **Run tests before committing** code changes
2. **Use diagnostic script** when debugging integration issues
3. **Enable DEBUG logging** when investigating failures
4. **Test with real API** periodically (diagnostic script)
5. **Clean up test data** from vector stores regularly
6. **Monitor OpenAI quota** usage during testing
7. **Mock external calls** in unit tests for speed and reliability

## Getting Help

If tests fail:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Run diagnostic script: `python test_mcp_connection.py`
3. Enable DEBUG logging
4. Review test output carefully
5. Check OpenAI API status: https://status.openai.com/

