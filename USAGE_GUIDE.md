# MCP Tool Usage Guide

This guide explains how to use the Context DB MCP tools efficiently in Cursor.

## 🔧 Available Tools

The Context DB MCP server provides two tools for managing context in OpenAI vector stores:

1. **`ingest_document`** - Store documents/summaries in the vector store
2. **`retrieve_relevant_chunks`** - Search and retrieve relevant content

---

## 📥 Tool 1: ingest_document

### Purpose
Add plain-text documents, feature summaries, or code documentation into the configured OpenAI vector store for future retrieval.

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | The plain-text content to ingest. **Must not be empty.** |

### Optional Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `vector_store_id` | string | Target vector store ID. If omitted, uses default from config. |
| `vector_store_name` | string | Vector store name to create/find. Only used if `vector_store_id` is not provided. |
| `document_id` | string | Stable identifier for the document (stored as file attribute). Useful for tracking. |
| `filename` | string | Logical filename for the uploaded document. Auto-generated if omitted. |
| `summary` | string | High-level summary or title (stored as attribute). Helps with organization. |
| `attributes` | object | Additional key/value pairs to attach as file attributes. Use for custom metadata. |
| `chunking_strategy` | object | OpenAI chunking strategy configuration. Advanced usage only. |
| `mime_type` | string | MIME type of the file. Defaults to `'text/plain'`. |

### Example Usage

#### Minimal Example (Only Required Parameters)
```json
{
  "content": "This is my document content that I want to store for later retrieval."
}
```

#### Recommended Example (With Metadata)
```json
{
  "content": "User authentication is handled by the AuthService class in src/auth/service.py. It uses JWT tokens and validates them against the database.",
  "document_id": "feature-auth-2025-11-06",
  "summary": "User authentication feature implementation",
  "filename": "auth-feature-summary.txt",
  "attributes": {
    "feature": "authentication",
    "date": "2025-11-06",
    "author": "developer"
  }
}
```

#### Complete Example (All Parameters)
```json
{
  "content": "Detailed implementation notes...",
  "vector_store_id": "vs_abc123",
  "document_id": "doc-12345",
  "filename": "implementation-notes.txt",
  "summary": "Feature X Implementation Notes",
  "attributes": {
    "project": "MyApp",
    "component": "backend",
    "version": "2.0"
  },
  "chunking_strategy": {
    "type": "auto"
  },
  "mime_type": "text/plain"
}
```

### Response Format

The tool returns an object with the following fields:

```json
{
  "vector_store_id": "vs_abc123",
  "vector_store_name": "cursor-context-db",
  "file_id": "file_xyz789",
  "filename": "auth-feature-summary.txt",
  "status": "completed",
  "attributes": {
    "document_id": "feature-auth-2025-11-06",
    "summary": "User authentication feature implementation",
    "ingested_at": "2025-11-06T10:30:00.000Z"
  }
}
```

### Best Practices

1. **Always include `document_id` and `summary`** - Makes documents easier to find and filter later
2. **Use descriptive filenames** - Helps identify content without reading the full text
3. **Add custom attributes** - Use for filtering (e.g., by date, feature, component)
4. **Keep content focused** - One document per feature/topic works better than large mixed documents
5. **Use consistent naming** - Establish patterns for `document_id` (e.g., `feature-name-YYYY-MM-DD`)

---

## 🔍 Tool 2: retrieve_relevant_chunks

### Purpose
Search the configured OpenAI vector store for chunks most relevant to a provided query. Returns text snippets ranked by similarity score.

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | The search query that drives similarity search. **Must not be empty.** |

### Optional Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `vector_store_id` | string | Vector store to query. If omitted, uses default from config. |
| `max_results` | integer | Maximum number of chunks to return. Range: 1-50. Default from config. |
| `score_threshold` | float | Minimum similarity score (0.0-1.0) for inclusion. Higher = more strict. |
| `attributes_filter` | object | Exact-match filters on file attributes (e.g., `{"feature": "auth"}`). |
| `rewrite_query` | boolean | Enable/disable OpenAI's automatic query rewriting. Default: enabled. |

### Example Usage

#### Minimal Example (Only Required Parameters)
```json
{
  "query": "How does user authentication work?"
}
```

#### Recommended Example (With Limits)
```json
{
  "query": "How does user authentication work?",
  "max_results": 5,
  "score_threshold": 0.7
}
```

#### Advanced Example (With Filtering)
```json
{
  "query": "database connection pooling implementation",
  "max_results": 10,
  "score_threshold": 0.6,
  "attributes_filter": {
    "component": "backend",
    "feature": "database"
  }
}
```

### Response Format

The tool returns an object with the following structure:

```json
{
  "vector_store_id": "vs_abc123",
  "query": "How does user authentication work?",
  "results": [
    {
      "file_id": "file_xyz789",
      "filename": "auth-feature-summary.txt",
      "score": 0.89,
      "text": "User authentication is handled by the AuthService class in src/auth/service.py. It uses JWT tokens and validates them against the database.",
      "attributes": {
        "document_id": "feature-auth-2025-11-06",
        "summary": "User authentication feature implementation",
        "ingested_at": "2025-11-06T10:30:00.000Z",
        "feature": "authentication"
      }
    },
    {
      "file_id": "file_abc456",
      "filename": "security-notes.txt",
      "score": 0.82,
      "text": "JWT tokens expire after 24 hours and are validated using the SECRET_KEY environment variable.",
      "attributes": {
        "document_id": "security-2025-11-05",
        "summary": "Security implementation details"
      }
    }
  ]
}
```

### Understanding Scores

Similarity scores range from 0.0 to 1.0:

- **0.9 - 1.0**: Highly relevant, almost exact match
- **0.8 - 0.9**: Very relevant, strong semantic match
- **0.7 - 0.8**: Relevant, good semantic match
- **0.6 - 0.7**: Moderately relevant, partial match
- **< 0.6**: Weakly relevant, may be noise

**Recommendation**: Start with `score_threshold: 0.7` and adjust based on results.

### Best Practices

1. **Use natural language queries** - Write as if asking a colleague: "How does X work?"
2. **Set appropriate thresholds** - Use `score_threshold: 0.7` to filter out weak matches
3. **Limit results** - Use `max_results: 5-10` to get focused, high-quality results
4. **Filter by attributes** - Use `attributes_filter` to narrow down to specific components/features
5. **Iterate on queries** - If results are poor, try rephrasing your query more specifically

---

## 🎯 Common Use Cases

### Use Case 1: Storing Feature Implementation Summary

After implementing a feature, store a summary for future reference:

```json
{
  "content": "Implemented user authentication using JWT tokens. The AuthService class in src/auth/service.py handles login, token generation, and validation. Tokens expire after 24 hours and are stored in HTTP-only cookies. Password hashing uses bcrypt with salt factor 12.",
  "document_id": "feature-auth-implementation",
  "summary": "User authentication feature implementation",
  "filename": "auth-implementation.txt",
  "attributes": {
    "feature": "authentication",
    "component": "backend",
    "date": "2025-11-06",
    "files_modified": "src/auth/service.py, src/auth/middleware.py"
  }
}
```

### Use Case 2: Finding Relevant Context for New Work

Before starting work on a related feature:

```json
{
  "query": "How is user authentication implemented?",
  "max_results": 5,
  "score_threshold": 0.75,
  "attributes_filter": {
    "component": "backend"
  }
}
```

### Use Case 3: Storing Bug Fix Details

After fixing a bug, document what was changed:

```json
{
  "content": "Fixed race condition in payment processing. The issue was in src/payments/processor.py where concurrent requests could double-charge users. Added database transaction locking using SELECT FOR UPDATE. Also added retry logic with exponential backoff.",
  "document_id": "bugfix-payment-race-condition",
  "summary": "Payment race condition fix",
  "filename": "payment-bugfix.txt",
  "attributes": {
    "type": "bugfix",
    "component": "payments",
    "date": "2025-11-06",
    "issue_id": "BUG-123"
  }
}
```

### Use Case 4: Retrieving Bug Fix History

When investigating a similar issue:

```json
{
  "query": "payment processing race conditions concurrency issues",
  "max_results": 10,
  "score_threshold": 0.6,
  "attributes_filter": {
    "type": "bugfix",
    "component": "payments"
  }
}
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ Don't: Empty or Too Short Content
```json
{
  "content": "Fixed bug"  // Too vague, not useful
}
```

### ✅ Do: Provide Detailed Content
```json
{
  "content": "Fixed bug where users couldn't log in with uppercase emails. Added case-insensitive email comparison in src/auth/service.py:45. Updated tests in tests/auth/test_login.py."
}
```

---

### ❌ Don't: Skip Metadata
```json
{
  "content": "Very long detailed content..."
  // No document_id, summary, or attributes
}
```

### ✅ Do: Include Useful Metadata
```json
{
  "content": "Very long detailed content...",
  "document_id": "feature-payments-2025-11-06",
  "summary": "Payment gateway integration",
  "attributes": {
    "feature": "payments",
    "component": "backend"
  }
}
```

---

### ❌ Don't: Use Too Generic Queries
```json
{
  "query": "code"  // Way too broad
}
```

### ✅ Do: Be Specific
```json
{
  "query": "How does the payment processing workflow handle refunds?"
}
```

---

### ❌ Don't: Return Too Many Results
```json
{
  "query": "authentication",
  "max_results": 50  // Too many, hard to process
}
```

### ✅ Do: Limit to Relevant Results
```json
{
  "query": "authentication",
  "max_results": 5,
  "score_threshold": 0.75  // Only high-quality matches
}
```

---

## 🔄 Workflow Example

Here's a complete workflow showing how to use both tools together:

### Step 1: Implement a Feature
You just finished implementing a new dashboard feature.

### Step 2: Store the Summary
```json
{
  "content": "Implemented admin dashboard in src/admin/dashboard.py. Features include: user management, analytics charts using Chart.js, real-time data updates via WebSockets. The dashboard is accessible at /admin/dashboard and requires admin role. Updated permissions in src/auth/permissions.py.",
  "document_id": "feature-admin-dashboard-2025-11-06",
  "summary": "Admin dashboard implementation",
  "filename": "admin-dashboard.txt",
  "attributes": {
    "feature": "dashboard",
    "component": "admin",
    "date": "2025-11-06",
    "files": "src/admin/dashboard.py, src/auth/permissions.py"
  }
}
```

### Step 3: Later, When Working on Related Feature
You need to add a new chart to the dashboard.

```json
{
  "query": "How is the admin dashboard implemented? What charting library is used?",
  "max_results": 5,
  "score_threshold": 0.7,
  "attributes_filter": {
    "feature": "dashboard"
  }
}
```

### Step 4: Get Relevant Context
The retrieval returns your earlier summary, showing you that Chart.js is used and the dashboard is in `src/admin/dashboard.py`. You can now proceed with adding the new chart with full context!

---

## 📊 Performance Tips

1. **Smaller is Better**: Store focused documents rather than dumping entire codebases
2. **Use Filters**: `attributes_filter` significantly speeds up searches
3. **Set Thresholds**: `score_threshold` reduces noise and processing time
4. **Limit Results**: Don't request more chunks than you'll actually use
5. **Consistent Metadata**: Use consistent attribute keys for easier filtering

---

## 🆘 Troubleshooting

### Problem: No Results Returned
**Solutions**:
- Lower `score_threshold` (try 0.5 or 0.6)
- Increase `max_results`
- Make query more general
- Remove `attributes_filter` to search all documents

### Problem: Too Many Irrelevant Results
**Solutions**:
- Raise `score_threshold` (try 0.8 or 0.9)
- Make query more specific
- Add `attributes_filter` to narrow scope
- Reduce `max_results`

### Problem: Documents Not Being Found
**Solutions**:
- Check that ingestion was successful (status: "completed")
- Verify you're using the correct `vector_store_id`
- Check attribute filters aren't too restrictive

---

## 📚 Additional Resources

- **QUICKSTART.md** - Get started in 5 minutes
- **TROUBLESHOOTING.md** - Solve common configuration issues
- **TESTING_GUIDE.md** - Test your MCP server
- **README.md** - Full project documentation

For more help, run the diagnostic script:
```bash
python test_mcp_connection.py
```

