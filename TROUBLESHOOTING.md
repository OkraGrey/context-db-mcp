# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Context DB MCP server.

## Quick Diagnostic

Run the diagnostic script first:

```bash
cd /path/to/Context_DB_MCP
python test_mcp_connection.py
```

This will check:
- ✅ Environment configuration
- ✅ OpenAI API connectivity
- ✅ Vector store access
- ✅ Document ingestion
- ✅ Document retrieval

---

## Common Issues

### 1. "OPENAI_API_KEY not found in environment"

**Symptom**: The MCP server fails to start or tools don't work in Cursor.

**Solution**:

1. Create a `.env` file in the project root (copy from `env.example`):
   ```bash
   cp env.example .env
   ```

2. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. For Cursor integration, set it in `~/.cursor/mcp.json`:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "context-db-mcp",
         "env": {
           "OPENAI_API_KEY": "sk-your-actual-api-key-here",
           "CONTEXT_DB_VECTOR_STORE_NAME": "cursor-context-db"
         }
       }
     }
   }
   ```

4. **Important**: Use your actual API key, NOT `${OPENAI_API_KEY}` variable substitution
   - Variable substitution doesn't always work in Cursor's MCP config
   - Hardcode the key or use Cursor's secrets management if available

---

### 2. "No vector store identifier was provided"

**Symptom**: Tools fail with error about missing vector store configuration.

**Solution**:

Add one of these to your `.env` file:

**Option A** - Use an existing vector store:
```
CONTEXT_DB_VECTOR_STORE_ID=vs_xxxxxxxxxxxxx
```

**Option B** - Create/find by name (recommended):
```
CONTEXT_DB_VECTOR_STORE_NAME=cursor-context-db
```

The server will automatically find or create a vector store with that name.

---

### 3. "Failed to connect to OpenAI API"

**Symptom**: Connection errors or timeout messages.

**Causes & Solutions**:

1. **Invalid API key**
   - Verify your key at https://platform.openai.com/api-keys
   - Make sure it starts with `sk-`
   - Check for extra spaces or quotes

2. **Network issues**
   - Check your internet connection
   - Verify you're not behind a restrictive firewall
   - Try accessing https://api.openai.com/v1/models in your browser

3. **API quota exceeded**
   - Check your OpenAI usage at https://platform.openai.com/usage
   - Verify your account has billing enabled

---

### 4. Cursor shows "MCP connection failed" or tools not available

**Symptom**: MCP server doesn't appear in Cursor or tools are unavailable.

**Solutions**:

1. **Check MCP configuration file location**:
   - macOS/Linux: `~/.cursor/mcp.json`
   - Windows: `%USERPROFILE%\.cursor\mcp.json`

2. **Verify the configuration format**:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "context-db-mcp",
         "env": {
           "OPENAI_API_KEY": "sk-your-key-here",
           "CONTEXT_DB_VECTOR_STORE_NAME": "cursor-context-db",
           "CONTEXT_DB_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

3. **Verify the command is in PATH**:
   ```bash
   which context-db-mcp
   # Should show: /path/to/env/bin/context-db-mcp
   ```

   If not found, use the full path:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "/absolute/path/to/env/bin/context-db-mcp",
         ...
       }
     }
   }
   ```

4. **Check Cursor logs**:
   - Open Cursor DevTools: Help → Toggle Developer Tools
   - Look for MCP-related errors in the Console tab
   - Check for environment variable issues

5. **Restart Cursor completely**:
   - Quit Cursor entirely (not just close window)
   - Reopen and wait 10-15 seconds for MCP servers to connect

---

### 5. "Document ingestion succeeds but retrieval returns no results"

**Symptom**: `ingest_document` works but `retrieve_relevant_chunks` returns empty results.

**Causes & Solutions**:

1. **Documents still processing**
   - Vector store files need time to be indexed (usually 10-30 seconds)
   - Wait a minute and try again
   - Check file status in OpenAI dashboard

2. **Query doesn't match content**
   - Try broader queries
   - Use keywords that appear in your documents
   - Check the `score_threshold` isn't too high

3. **Wrong vector store**
   - Verify you're querying the same store you ingested to
   - Check `vector_store_id` in both calls

4. **Files failed to process**
   - Check OpenAI dashboard for failed files
   - Verify content is plain text (not binary)
   - Ensure content isn't empty or too short

---

### 6. "Rate limit exceeded" or "Quota exceeded"

**Symptom**: API calls fail with rate limit errors.

**Solutions**:

1. **Check your OpenAI plan limits**:
   - Free tier: Very limited API access
   - Pay-as-you-go: Check billing at https://platform.openai.com/settings/organization/billing

2. **Reduce request frequency**:
   - Add `CONTEXT_DB_REQUEST_TIMEOUT_SECONDS=180` to `.env`
   - Batch your ingestion calls
   - Use lower `max_results` for retrieval

3. **Upgrade your OpenAI plan**:
   - Consider upgrading to a paid plan with higher limits

---

### 7. "Permission denied" or "Authorization failed"

**Symptom**: API calls fail with permission errors.

**Causes & Solutions**:

1. **API key doesn't have vector store access**
   - Ensure your OpenAI account has access to Assistants v2 API
   - This requires a paid account in most cases

2. **Wrong organization/project**
   - If using organization IDs, verify they're correct:
     ```
     CONTEXT_DB_OPENAI_ORGANIZATION=org-xxxxx
     CONTEXT_DB_OPENAI_PROJECT=proj-xxxxx
     ```

3. **API key revoked or expired**
   - Generate a new API key at https://platform.openai.com/api-keys

---

### 8. MCP tools work in one Cursor session but not another

**Symptom**: Different behavior across different projects/sessions.

**Solution**:

1. **MCP config is global, not per-project**
   - `~/.cursor/mcp.json` applies to all Cursor windows
   - Environment variables are shared

2. **Vector stores are separate**
   - Each session might be using different vector stores
   - Use consistent `CONTEXT_DB_VECTOR_STORE_NAME` or `CONTEXT_DB_VECTOR_STORE_ID`

3. **Per-project configuration** (if needed):
   - You can specify different vector stores per call:
     ```python
     ingest_document(
       content="...",
       vector_store_name="project-specific-store"
     )
     ```

---

## Debug Mode

Enable detailed logging:

1. **In `.env` file**:
   ```
   CONTEXT_DB_LOG_LEVEL=DEBUG
   ```

2. **In Cursor MCP config**:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "context-db-mcp",
         "env": {
           "OPENAI_API_KEY": "sk-...",
           "CONTEXT_DB_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

3. **View logs in Cursor**:
   - Open DevTools: Help → Toggle Developer Tools
   - Check Console tab for detailed MCP logs

---

## Testing the Server Directly

Test without Cursor:

```bash
# Activate virtual environment
source env/bin/activate  # or env\Scripts\activate on Windows

# Run diagnostic
python test_mcp_connection.py

# Run unit tests
pytest tests/

# Start server manually (for debugging)
context-db-mcp
```

---

## Verification Checklist

Before opening an issue, verify:

- [ ] `OPENAI_API_KEY` is set correctly
- [ ] API key has vector store access (paid account)
- [ ] `context-db-mcp` command is in PATH or full path is used
- [ ] Cursor MCP config file exists and is valid JSON
- [ ] Cursor has been completely restarted
- [ ] Diagnostic script passes all checks: `python test_mcp_connection.py`
- [ ] Unit tests pass: `pytest tests/`
- [ ] OpenAI account has available quota

---

## Still Having Issues?

1. **Run the diagnostic script**:
   ```bash
   python test_mcp_connection.py
   ```

2. **Check the logs**:
   - Enable DEBUG logging
   - Look for specific error messages

3. **Test with minimal config**:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "context-db-mcp",
         "env": {
           "OPENAI_API_KEY": "sk-your-actual-key",
           "CONTEXT_DB_VECTOR_STORE_NAME": "test-store",
           "CONTEXT_DB_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

4. **Verify OpenAI API access independently**:
   ```python
   from openai import OpenAI
   client = OpenAI(api_key="sk-...")
   stores = list(client.vector_stores.list())
   print(f"Found {len(stores)} vector stores")
   ```

---

## Getting Help

When reporting issues, include:

1. Output from `python test_mcp_connection.py`
2. Your MCP config (with API key redacted)
3. Cursor version and OS
4. Relevant error messages from Cursor DevTools Console
5. Whether the issue is with ingestion, retrieval, or both


