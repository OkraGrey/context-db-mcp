# Quick Start Guide

Get your Context DB MCP server up and running in 5 minutes.

## Step 1: Set up your environment

1. **Create a `.env` file** (copy from `env.example`):
   ```bash
   cp env.example .env
   ```

2. **Add your OpenAI API key** in `.env`:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   CONTEXT_DB_VECTOR_STORE_NAME=cursor-context-db
   ```

   Get your API key from: https://platform.openai.com/api-keys

   > ⚠️ **Important**: You need a paid OpenAI account with access to the Assistants v2 API (vector stores).

## Step 2: Install the package

```bash
# Activate your virtual environment if not already active
source env/bin/activate  # or env\Scripts\activate on Windows

# Install the package
pip install -e .

# Verify installation
context-db-mcp --help  # This should error but shows the command exists
```

## Step 3: Test your setup

Run the diagnostic script to verify everything works:

```bash
python test_mcp_connection.py
```

You should see all checks pass:
- ✅ Environment Configuration
- ✅ OpenAI API Connection
- ✅ Vector Store Access
- ✅ Document Ingestion
- ✅ Chunk Retrieval

If anything fails, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Step 4: Configure Cursor

1. **Create or edit** `~/.cursor/mcp.json`:
   ```bash
   # On macOS/Linux
   mkdir -p ~/.cursor
   touch ~/.cursor/mcp.json
   
   # On Windows
   # Create %USERPROFILE%\.cursor\mcp.json
   ```

2. **Add this configuration**:
   ```json
   {
     "servers": {
       "context-db": {
         "command": "context-db-mcp",
         "env": {
           "OPENAI_API_KEY": "sk-your-actual-api-key-here",
           "CONTEXT_DB_VECTOR_STORE_NAME": "cursor-context-db",
           "CONTEXT_DB_LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

   > 💡 **Tip**: If `context-db-mcp` is not in your PATH, use the full path:
   > ```json
   > "command": "/absolute/path/to/Context_DB_MCP/env/bin/context-db-mcp"
   > ```

3. **Restart Cursor completely** (quit and reopen, not just close window)

## Step 5: Verify in Cursor

1. **Open Cursor Developer Tools**:
   - Menu: Help → Toggle Developer Tools
   - Look at the Console tab

2. **Check for MCP connection**:
   - You should see logs about MCP servers connecting
   - Look for "context-db" in the logs

3. **Test the tools**:
   - Start a new chat in Cursor
   - Ask the AI: "Can you use the ingest_document tool to store a test note?"
   - The AI should be able to call the MCP tool

## Quick Test in Cursor

Try these commands with the AI:

### 1. Ingest a document:
```
Use the ingest_document tool to store this information:

Content: "Project uses FastAPI for the backend API. Main entry point is src/main.py. Database models are in src/models/."

Summary: "Backend architecture overview"

Document ID: "backend-arch-v1"
```

### 2. Retrieve information:
```
Use retrieve_relevant_chunks to find information about "backend API framework"
```

You should get back the context you just stored!

## Common First-Time Issues

### "MCP server not found" or "tools not available"

**Solution**:
1. Check that `context-db-mcp` is in your PATH:
   ```bash
   which context-db-mcp  # macOS/Linux
   where context-db-mcp  # Windows
   ```
2. If not found, use the full path in mcp.json
3. Completely restart Cursor

### "API key not found" or "Permission denied"

**Solution**:
1. Make sure your API key in `~/.cursor/mcp.json` is the actual key (starts with `sk-`)
2. Don't use environment variable syntax like `${OPENAI_API_KEY}` - use the actual key
3. Verify your key at: https://platform.openai.com/api-keys

### "No vector store identifier provided"

**Solution**:
Add this to your mcp.json env section:
```json
"CONTEXT_DB_VECTOR_STORE_NAME": "cursor-context-db"
```

### Documents ingest but retrieval returns nothing

**Solution**:
Wait 30-60 seconds after ingesting for OpenAI to process and index the documents, then try retrieval again.

## Next Steps

Once everything works:

1. **Read the full [README](README.md)** for advanced usage patterns
2. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** if you encounter issues
3. **Run unit tests** to ensure everything is properly configured:
   ```bash
   pip install -e ".[dev]"
   pytest tests/ -v
   ```

## Pro Tips

1. **Use descriptive document IDs** for easy tracking:
   ```
   document_id: "feature-auth-2024-11-06"
   ```

2. **Add summaries** to make retrieval more accurate:
   ```
   summary: "User authentication implementation details"
   ```

3. **Use custom attributes** for filtering:
   ```json
   {
     "attributes": {
       "feature": "auth",
       "date": "2024-11-06",
       "status": "completed"
     }
   }
   ```

4. **Query with specific keywords** from your ingested content for better results

5. **Ingest regularly** after significant changes or at the end of each session

## Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Run `python test_mcp_connection.py` to diagnose problems
- Verify tests pass: `pytest tests/ -v`
- Enable DEBUG logging in mcp.json: `"CONTEXT_DB_LOG_LEVEL": "DEBUG"`

Happy coding! 🚀

