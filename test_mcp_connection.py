#!/usr/bin/env python3
"""
Diagnostic script to test Context DB MCP server connection and functionality.

This script performs comprehensive checks:
1. Environment configuration validation
2. OpenAI API connectivity
3. Vector store access/creation
4. Document ingestion
5. Document retrieval

Run this script to diagnose issues before using the MCP server in Cursor.

Usage:
    python test_mcp_connection.py
"""

import os
import sys
from datetime import datetime

try:
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please install dependencies: pip install openai python-dotenv")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text):
    """Print an info message."""
    print(f"  {text}")


def check_environment():
    """Check environment configuration."""
    print_header("1. Checking Environment Configuration")
    
    # Load .env file if it exists
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print_success(f"Loaded .env file from {env_path}")
    else:
        print_warning(f"No .env file found at {env_path}")
        print_info("Environment variables will be read from system environment")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CONTEXT_DB_OPENAI_API_KEY")
    if not api_key:
        print_error("OPENAI_API_KEY not found in environment")
        print_info("Set it in .env file or as an environment variable:")
        print_info("  export OPENAI_API_KEY='sk-...'")
        return False
    
    # Mask the API key for display
    masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
    print_success(f"OPENAI_API_KEY found: {masked_key}")
    
    # Check optional settings
    vector_store_id = os.getenv("CONTEXT_DB_VECTOR_STORE_ID")
    vector_store_name = os.getenv("CONTEXT_DB_VECTOR_STORE_NAME")
    
    if vector_store_id:
        print_success(f"CONTEXT_DB_VECTOR_STORE_ID: {vector_store_id}")
    elif vector_store_name:
        print_success(f"CONTEXT_DB_VECTOR_STORE_NAME: {vector_store_name}")
    else:
        print_warning("No default vector store configured")
        print_info("Set CONTEXT_DB_VECTOR_STORE_NAME in your .env file")
        print_info("The server will create a new store on demand")
    
    return True


def check_openai_connection(api_key):
    """Check OpenAI API connectivity."""
    print_header("2. Testing OpenAI API Connection")
    
    try:
        client = OpenAI(api_key=api_key, timeout=10.0)
        print_info("Creating OpenAI client...")
        
        # Test API connection by listing models
        models = client.models.list()
        print_success(f"Successfully connected to OpenAI API")
        print_info(f"Found {len(list(models))} available models")
        
        return client
    except Exception as e:
        print_error(f"Failed to connect to OpenAI API: {e}")
        print_info("Check your API key and internet connection")
        return None


def check_vector_store_access(client):
    """Check vector store access."""
    print_header("3. Testing Vector Store Access")
    
    vector_store_id = os.getenv("CONTEXT_DB_VECTOR_STORE_ID")
    vector_store_name = os.getenv("CONTEXT_DB_VECTOR_STORE_NAME") or "mcp-test-store"
    
    try:
        # Try to list existing stores
        print_info("Listing existing vector stores...")
        stores = list(client.vector_stores.list(limit=5))
        print_success(f"Found {len(stores)} existing vector stores")
        
        if stores:
            print_info("Recent vector stores:")
            for store in stores[:3]:
                store_name = getattr(store, 'name', 'Unnamed')
                print_info(f"  - {store.id}: {store_name}")
        
        # If specific store ID is configured, try to access it
        if vector_store_id:
            print_info(f"Retrieving configured vector store: {vector_store_id}")
            store = client.vector_stores.retrieve(vector_store_id)
            print_success(f"Successfully accessed vector store: {store.id}")
            return store
        
        # Otherwise, find or create by name
        print_info(f"Looking for vector store named: {vector_store_name}")
        for store in stores:
            if getattr(store, 'name', None) == vector_store_name:
                print_success(f"Found existing vector store: {store.id}")
                return store
        
        # Create new store
        print_info(f"Creating new vector store: {vector_store_name}")
        store = client.vector_stores.create(
            name=vector_store_name,
            metadata={"created_by": "mcp-test-script", "created_at": datetime.now().isoformat()}
        )
        print_success(f"Created new vector store: {store.id}")
        print_warning("Remember to add this to your .env file:")
        print_info(f"  CONTEXT_DB_VECTOR_STORE_ID={store.id}")
        
        return store
        
    except Exception as e:
        print_error(f"Failed to access vector stores: {e}")
        return None


def test_ingest_document(client, vector_store):
    """Test document ingestion."""
    print_header("4. Testing Document Ingestion")
    
    try:
        # Create test document
        test_content = f"""
Test Document for MCP Diagnostic
=================================

This is a test document created at {datetime.now().isoformat()}.

It contains information about:
- User authentication flow
- Database schema migrations
- API endpoint documentation
- Error handling patterns

This document is used to verify that the Context DB MCP server
can successfully ingest and retrieve documents from the vector store.
"""
        
        print_info("Creating test document...")
        
        # Upload to vector store
        from io import BytesIO
        buffer = BytesIO(test_content.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"mcp-test-{int(datetime.now().timestamp())}.txt"
        
        print_info(f"Uploading document: {filename}")
        vector_store_file = client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=(filename, buffer, "text/plain"),
            attributes={
                "document_id": "mcp-test-doc",
                "summary": "MCP Diagnostic Test Document",
                "test": "true"
            }
        )
        
        print_success(f"Document uploaded: {vector_store_file.id}")
        print_info(f"Status: {vector_store_file.status}")
        
        if vector_store_file.status == "completed":
            print_success("Document processing completed successfully")
            return vector_store_file
        else:
            print_warning(f"Document status is: {vector_store_file.status}")
            print_info("This might cause issues with retrieval")
            return vector_store_file
        
    except Exception as e:
        print_error(f"Failed to ingest document: {e}")
        import traceback
        print_info(traceback.format_exc())
        return None


def test_retrieve_chunks(client, vector_store):
    """Test chunk retrieval."""
    print_header("5. Testing Chunk Retrieval")
    
    try:
        test_query = "authentication and error handling"
        
        print_info(f"Searching for: '{test_query}'")
        
        results = client.vector_stores.search(
            vector_store.id,
            query=test_query,
            max_num_results=5
        )
        
        results_list = list(results)
        
        if not results_list:
            print_warning("No results found")
            print_info("This might be expected if documents are still processing")
            print_info("Wait a few seconds and try running the test again")
            return False
        
        print_success(f"Found {len(results_list)} matching chunks")
        
        for i, result in enumerate(results_list[:3], 1):
            print_info(f"\nResult {i}:")
            print_info(f"  File: {result.filename}")
            print_info(f"  Score: {result.score:.3f}")
            
            # Extract text content
            text_content = []
            for chunk in result.content:
                if chunk.type == "text":
                    text_preview = chunk.text[:100].replace('\n', ' ')
                    text_content.append(text_preview)
            
            if text_content:
                print_info(f"  Preview: {text_content[0]}...")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to retrieve chunks: {e}")
        import traceback
        print_info(traceback.format_exc())
        return False


def print_summary(checks_passed):
    """Print test summary."""
    print_header("Test Summary")
    
    total = len(checks_passed)
    passed = sum(checks_passed.values())
    
    for check_name, passed_check in checks_passed.items():
        if passed_check:
            print_success(check_name)
        else:
            print_error(check_name)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} checks passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All checks passed! Your MCP server should work correctly.{Colors.RESET}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some checks failed. Please fix the issues above.{Colors.RESET}\n")
        return False


def main():
    """Run all diagnostic tests."""
    print(f"{Colors.BOLD}Context DB MCP Diagnostic Tool{Colors.RESET}")
    print("This script will verify your MCP server setup\n")
    
    checks_passed = {}
    
    # 1. Check environment
    env_ok = check_environment()
    checks_passed["Environment Configuration"] = env_ok
    if not env_ok:
        print_summary(checks_passed)
        return 1
    
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CONTEXT_DB_OPENAI_API_KEY")
    
    # 2. Check OpenAI connection
    client = check_openai_connection(api_key)
    checks_passed["OpenAI API Connection"] = client is not None
    if not client:
        print_summary(checks_passed)
        return 1
    
    # 3. Check vector store access
    vector_store = check_vector_store_access(client)
    checks_passed["Vector Store Access"] = vector_store is not None
    if not vector_store:
        print_summary(checks_passed)
        return 1
    
    # 4. Test ingestion
    uploaded_file = test_ingest_document(client, vector_store)
    checks_passed["Document Ingestion"] = uploaded_file is not None
    
    # 5. Test retrieval (may fail if documents are still processing)
    retrieval_ok = test_retrieve_chunks(client, vector_store)
    checks_passed["Chunk Retrieval"] = retrieval_ok
    
    # Print summary
    success = print_summary(checks_passed)
    
    # Additional guidance
    if success:
        print(f"{Colors.BOLD}Next Steps:{Colors.RESET}")
        print("1. Make sure your Cursor MCP config (~/.cursor/mcp.json) is correct")
        print("2. Restart Cursor to load the MCP server")
        print("3. Try the ingest_document and retrieve_relevant_chunks tools")
        print(f"\nExample Cursor MCP config:")
        print(f'{Colors.YELLOW}{{\n  "servers": {{\n    "context-db": {{\n      "command": "context-db-mcp",\n      "env": {{\n        "OPENAI_API_KEY": "${{OPENAI_API_KEY}}",\n        "CONTEXT_DB_VECTOR_STORE_ID": "{vector_store.id}"\n      }}\n    }}\n  }}\n}}{Colors.RESET}\n')
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

