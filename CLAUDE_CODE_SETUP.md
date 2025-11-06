# Claude Code Setup Guide

This guide explains how to register the Context DB MCP server with Claude Code (Anthropic's IDE).

## Prerequisites

Before you begin, ensure you have:

1. ✅ Claude Code installed (from Anthropic)
2. ✅ Context DB MCP server installed (`pip install -e .`)
3. ✅ OpenAI API key with Assistants v2 API access
4. ✅ Python 3.11+ with the virtual environment activated

## Quick Setup

### Step 1: Create Configuration Directory

```bash
mkdir -p ~/.anthropic
```

### Step 2: Create Configuration File

Create or edit `~/.anthropic/config.json`:

```bash
nano ~/.anthropic/config.json
# or use your preferred editor
```

### Step 3: Add MCP Server Configuration

Add the following configuration:

```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-actual-api-key-here",
        "CONTEXT_DB_VECTOR_STORE_NAME": "claude-shared-context"
      }
    }
  }
}
```

**Important**: Replace `sk-your-actual-api-key-here` with your actual OpenAI API key!

### Step 4: Restart Claude Code

Completely quit and restart Claude Code:
- Mac: Cmd+Q to quit, then relaunch
- Windows/Linux: Close all windows and relaunch

### Step 5: Verify Tools Are Available

In Claude Code, you should now see two MCP tools available:
- `mcp_context-db_ingest_document`
- `mcp_context-db_retrieve_relevant_chunks`

Try them out!

---

## Alternative: Using Full Path

If the `context-db-mcp` command isn't found, use the full path to the executable:

```json
{
  "mcpServers": {
    "context-db": {
      "command": "/Users/hasnainsohail/Documents/Computer/Nuts And Bolts/Self/Context_DB_MCP/env/bin/context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-actual-api-key-here",
        "CONTEXT_DB_VECTOR_STORE_NAME": "claude-shared-context"
      }
    }
  }
}
```

To find the full path:
```bash
which context-db-mcp
```

---

## Configuration Options

You can customize the MCP server behavior with additional environment variables:

### Minimal Configuration (Required Only)
```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-actual-api-key-here"
      }
    }
  }
}
```

### Recommended Configuration
```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-actual-api-key-here",
        "CONTEXT_DB_VECTOR_STORE_NAME": "claude-shared-context",
        "CONTEXT_DB_DEFAULT_MAX_RESULTS": "10",
        "CONTEXT_DB_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Complete Configuration (All Options)
```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-actual-api-key-here",
        "CONTEXT_DB_VECTOR_STORE_NAME": "claude-shared-context",
        "CONTEXT_DB_OPENAI_ORGANIZATION": "org-xxxxx",
        "CONTEXT_DB_OPENAI_PROJECT": "proj-xxxxx",
        "CONTEXT_DB_DEFAULT_MAX_RESULTS": "10",
        "CONTEXT_DB_REQUEST_TIMEOUT_SECONDS": "120",
        "CONTEXT_DB_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Configuration Options Explained

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | ✅ Yes | Your OpenAI API key | None |
| `CONTEXT_DB_VECTOR_STORE_NAME` | Recommended | Name of vector store to create/use | None |
| `CONTEXT_DB_VECTOR_STORE_ID` | Optional | Specific vector store ID (overrides name) | None |
| `CONTEXT_DB_OPENAI_ORGANIZATION` | Optional | OpenAI organization ID | None |
| `CONTEXT_DB_OPENAI_PROJECT` | Optional | OpenAI project ID | None |
| `CONTEXT_DB_DEFAULT_MAX_RESULTS` | Optional | Default number of chunks to return | 10 |
| `CONTEXT_DB_REQUEST_TIMEOUT_SECONDS` | Optional | API request timeout | 120 |
| `CONTEXT_DB_LOG_LEVEL` | Optional | Logging level (DEBUG/INFO/WARNING) | INFO |

---

## Multiple MCP Servers

You can add multiple MCP servers to the same configuration file:

```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key",
        "CONTEXT_DB_VECTOR_STORE_NAME": "claude-shared-context"
      }
    },
    "another-mcp-server": {
      "command": "some-other-mcp",
      "env": {
        "SOME_CONFIG": "value"
      }
    }
  }
}
```

---

## Testing the Connection

### Method 1: Use the Diagnostic Script

Before using the MCP in Claude Code, verify it works:

```bash
cd /Users/hasnainsohail/Documents/Computer/Nuts\ And\ Bolts/Self/Context_DB_MCP
python test_mcp_connection.py
```

This will perform 5 health checks:
1. ✅ Environment configuration
2. ✅ OpenAI API connectivity
3. ✅ Vector store access
4. ✅ Document ingestion
5. ✅ Document retrieval

All should pass before using in Claude Code.

### Method 2: Test in Claude Code

Once Claude Code is restarted, try this simple test:

**Test 1: Ingest a Document**

Ask Claude Code to:
```
Please ingest this test document:
Content: "This is a test document to verify the Context DB MCP is working in Claude Code."
Document ID: "test-claude-code-2025-11-06"
Summary: "Claude Code MCP test"
```

**Test 2: Retrieve the Document**

Then ask Claude Code to:
```
Please retrieve chunks with the query: "test document Claude Code verification"
```

You should get back the document you just ingested!

---

## Troubleshooting

### Problem: "Command not found: context-db-mcp"

**Solution 1**: Activate the virtual environment and reinstall:
```bash
cd /Users/hasnainsohail/Documents/Computer/Nuts\ And\ Bolts/Self/Context_DB_MCP
source env/bin/activate
pip install -e .
which context-db-mcp  # Note the path
```

Then use the full path in `config.json`.

**Solution 2**: Use absolute path in configuration:
```json
{
  "mcpServers": {
    "context-db": {
      "command": "/full/path/to/env/bin/context-db-mcp",
      "env": { ... }
    }
  }
}
```

### Problem: "OPENAI_API_KEY not found"

**Solution**: Make sure your API key is in the `config.json` file:
```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-actual-key-here"  ← Add this!
      }
    }
  }
}
```

### Problem: Tools Not Appearing in Claude Code

**Solution**:
1. Check the configuration file exists: `cat ~/.anthropic/config.json`
2. Verify JSON syntax is valid (use a JSON validator)
3. Completely quit Claude Code (don't just close the window)
4. Restart Claude Code
5. Check Claude Code's logs for errors

### Problem: Permission Denied

**Solution**: Make sure the script is executable:
```bash
chmod +x /path/to/env/bin/context-db-mcp
```

### Problem: API Authentication Errors

**Solution**:
1. Verify your API key is correct
2. Check you have a paid OpenAI account
3. Verify you have access to Assistants v2 API
4. Test the API key directly:
```bash
python test_mcp_connection.py
```

---

## Sharing Vector Store Between Cursor and Claude Code

You can use the same vector store in both Cursor and Claude Code by using the same `CONTEXT_DB_VECTOR_STORE_NAME`:

**In Cursor** (`~/.cursor/mcp.json`):
```json
{
  "servers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "CONTEXT_DB_VECTOR_STORE_NAME": "shared-context"
      }
    }
  }
}
```

**In Claude Code** (`~/.anthropic/config.json`):
```json
{
  "mcpServers": {
    "context-db": {
      "command": "context-db-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key",
        "CONTEXT_DB_VECTOR_STORE_NAME": "shared-context"
      }
    }
  }
}
```

Now documents ingested in Cursor can be retrieved in Claude Code and vice versa!

---

## Usage Examples in Claude Code

### Example 1: Store Implementation Summary

In Claude Code, say:
```
Please ingest this implementation summary:

Content: "Implemented the user authentication feature using JWT tokens. 
The AuthService class in src/auth/service.py handles login and token validation.
Tokens expire after 24 hours."

Document ID: "feature-auth-implementation"
Summary: "User authentication feature"
Filename: "auth-implementation.txt"
```

### Example 2: Retrieve Context

Before working on a related feature:
```
Please retrieve chunks about user authentication implementation.
Use max_results: 5 and score_threshold: 0.75
```

### Example 3: Store Bug Fix

After fixing a bug:
```
Please ingest this bug fix:

Content: "Fixed race condition in payment processing by adding database 
transaction locking. Modified src/payments/processor.py to use SELECT FOR UPDATE."

Document ID: "bugfix-payment-race-condition"
Summary: "Payment race condition fix"
Attributes: {"type": "bugfix", "component": "payments"}
```

---

## Best Practices

1. **Use Descriptive Names**: Give your vector store a meaningful name (e.g., `project-name-context`)
2. **Test First**: Run `python test_mcp_connection.py` before using in Claude Code
3. **Consistent Metadata**: Use consistent document IDs and attributes for easier retrieval
4. **Regular Ingestion**: Store summaries after completing features or fixing bugs
5. **Targeted Queries**: Use specific queries for better retrieval results

---

## Additional Resources

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Detailed tool documentation with examples
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[README.md](README.md)** - Full project documentation

---

## Support

If you encounter issues:

1. Run the diagnostic: `python test_mcp_connection.py`
2. Check `TROUBLESHOOTING.md`
3. Verify your configuration JSON syntax
4. Check Claude Code logs for error messages

Happy context managing! 🚀

