# Context DB MCP

A Model Context Protocol (MCP) server that stores and retrieves project context using OpenAI vector stores. Enable your AI editor to remember and recall project knowledge across sessions.

## Features

- **`ingest_document`** - Store project summaries, design docs, and context in a vector store
- **`retrieve_relevant_chunks`** - Retrieve relevant context using semantic search

## Installation

```bash
pip install -e .
```

**Requirements:** Python 3.11+ and an OpenAI API key

## Configuration

Create a `.env` file (or set environment variables):

```bash
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional - Vector Store (use ID for existing, NAME to create/find)
CONTEXT_DB_VECTOR_STORE_ID=vs_xxxxx
# OR
CONTEXT_DB_VECTOR_STORE_NAME=context-db-mcp

# Optional - Tuning
CONTEXT_DB_DEFAULT_MAX_RESULTS=10
CONTEXT_DB_REQUEST_TIMEOUT_SECONDS=120.0
CONTEXT_DB_LOG_LEVEL=INFO
```

Use `env.example` as a template.

## Usage

### Claude Code

Add to your project root inside .mcp.json (create with exact name and preceeding dot) and paste the following:

```json
{
  "mcpServers": {
    "context-db": {
      "command": "{PATH TO THE BIN FOLDER IN YOUR CLONED REPO for example: {YOUR PATH.....}/Context_DB_MCP/env/bin/context-db-mcp}",
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key-here",
        "CONTEXT_DB_VECTOR_STORE_NAME": "context-db-mcp"
      }
    }
  }
}
```

Restart Claude Code. Tools will be available as:
- `mcp__context-db__ingest_document`
- `mcp__context-db__retrieve_relevant_chunks`

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "context-db": {
      "command": "{PATH TO THE BIN FOLDER IN YOUR CLONED REPO for example: {YOUR PATH.....}/Context_DB_MCP/env/bin/context-db-mcp}",
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key-here",
        "CONTEXT_DB_VECTOR_STORE_NAME": "context-db-mcp"
      }
    }
  }
}
```

Restart Cursor and access the tools from the MCP integration panel.

## Testing

Run the diagnostic script to verify your setup:

```bash
python test_mcp_connection.py
```

Run the test suite:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```