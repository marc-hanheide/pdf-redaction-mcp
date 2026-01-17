# PDF Redaction MCP Server - AI Coding Instructions

## Project Overview

A Model Context Protocol (MCP) server for PDF redaction using **FastMCP 2.x** and **pymupdf**. This server provides 11 tools for session-based PDF operations - load, extract, search, redact text/images, save, and manage documents in memory. Version 0.2.0.

## Architecture

All tools register to a single `mcp = FastMCP("PDF Redaction Server")` instance at module level ([server.py](src/pdf_redaction_mcp/server.py)). Use `@mcp.tool()` decorator for all new tools.

### Session-Based In-Memory Workflow

**NEW in v0.2.0**: Documents are loaded into memory once and operated on without repeated file I/O.

- `DOCUMENT_STORE` dictionary: Maps `document_id` -> `pymupdf.Document` objects
- Documents persist in memory across multiple operations
- Explicit `load_pdf()` and `save_pdf()` for I/O control
- Use `close_pdf()` to free memory when done

### PDF Path Resolution

Only `load_pdf()` uses file paths. It uses `resolve_pdf_path()` to handle relative paths:
- If `--pdf-dir` is set, relative paths are resolved against it
- Absolute paths are used as-is
- Global `PDF_BASE_DIR` variable stores the configured base directory

All other tools work with `document_id` instead of file paths.

## Development Workflow

### Environment Setup

```bash
# Install dependencies (uses UV package manager)
uv sync

# Run tests
uv run pytest

# Run server locally (STDIO mode - default)
uv run pdf-redaction-mcp

# Run server with different transports
uv run pdf-redaction-mcp --transport sse --port 8000
uv run pdf-redaction-mcp --transport http --host 0.0.0.0 --port 8080

# Run with custom PDF base directory
uv run pdf-redaction-mcp --pdf-dir /path/to/pdfs

# Combine options
uv run pdf-redaction-mcp --transport sse --port 8000 --pdf-dir ./documents
```

### Testing Pattern

Tests in [tests/test_server.py](tests/test_server.py):
- Import functions directly from `pdf_redaction_mcp.server` module
- Handle FastMCP decoration: `if hasattr(fn, 'fn'): fn = fn.fn`
- Test error handling with non-existent document IDs (should return JSON with `"error"` key)
- No real PDF fixtures currently - tests focus on error handling and structure

### Adding New Tools

All tools work with in-memory documents (not file paths).

1. **Create the tool**:
   ```python
   @mcp.tool()
   def new_feature(document_id: str, ...) -> str:
       """Docstring explaining the tool."""
       try:
           # Check if document is loaded
           if document_id not in DOCUMENT_STORE:
               return json.dumps({
                   "error": f"Document '{document_id}' not found. Use load_pdf first.",
                   "available_documents": list(DOCUMENT_STORE.keys())
               })
           
           doc = DOCUMENT_STORE[document_id]
           # ... implementation (NO doc.close() - document stays in memory)
           return json.dumps(result)
       except Exception as e:
           return json.dumps({"error": str(e)})
   ```

2. **Always return JSON strings** for structured data or errors

3. **Never close documents** in operation tools - they remain in memory for multiple operations

4. **Add to README.md** in the Available Tools section

## Project Conventions

### Error Handling

Return errors as JSON strings (never raise exceptions to MCP client):
```python
except Exception as e:
    return json.dumps({"error": str(e)})
```

### Color Format

RGB tuples use 0-1 range, not 0-255: `(0, 0, 0)` for black, `(1, 0, 0)` for red ([server.py](src/pdf_redaction_mcp/server.py#L252)).

### Page Numbers

Always 0-indexed throughout the codebase. Display as 1-indexed only in user-facing text output.

### Document Cleanup

Only call `doc.close()` in the `close_pdf()` tool. All other tools leave documents in memory for reuse across operations.

### Coordinate System

Bounding boxes use pymupdf's format: `[x0, y0, x1, y1]` where:
- `(x0, y0)` = bottom-left corner
- `(x1, y1)` = top-right corner

## Key Files

- [src/pdf_redaction_mcp/server.py](src/pdf_redaction_mcp/server.py): Single file with all tools
- [pyproject.toml](pyproject.toml): UV-based dependency management, entry point: `pdf-redaction-mcp` script
- [examples/example_usage.py](examples/example_usage.py): Programmatic usage examples

## Dependencies

- `fastmcp>=2.0.0`: MCP framework (uses `@mcp.tool()` decorator)
- `pymupdf>=1.24.0`: PDF manipulation
- Python 3.10+ required

## Transport Modes

The server supports multiple transport modes via command line flags, but all modes work with local PDF files only:

**STDIO** (default): For Claude Desktop, Cursor, and desktop MCP clients
```bash
uv run pdf-redaction-mcp  # or --transport stdio
```

**SSE** (Server-Sent Events): For remote deployments
```bash
uv run pdf-redaction-mcp --transport sse --host 0.0.0.0 --port 8000
```

**HTTP**: For web-based clients
```bash
uv run pdf-redaction-mcp --transport http --port 8080
```

Entry point [server.py main()](src/pdf_redaction_mcp/server.py) uses argparse for configuration.

## Common Operations

### Load a PDF into memory
```python
load_pdf(pdf_path="document.pdf", document_id="doc1")  # Returns JSON with doc info
```

### Extract text with structure
```python
extract_text_from_pdf(document_id="doc1", format="blocks")  # Returns JSON with block-level info
```

### Search with regex
```python
search_text_in_pdf(document_id="doc1", search_string=r"\b\d{3}-\d{2}-\d{4}\b", use_regex=True)
```

### Redact by search (in-memory modification)
```python
redact_text_by_search(document_id="doc1", search_strings=["SSN", "John Doe"])
```

### Save modified document
```python
save_pdf(document_id="doc1", output_path="redacted.pdf")
```

### Verify redactions worked
```python
# Load both documents first
load_pdf(pdf_path="original.pdf", document_id="original")
load_pdf(pdf_path="redacted.pdf", document_id="redacted")

# Verify
verify_redactions(
    original_document_id="original",
    redacted_document_id="redacted",
    search_strings=["SSN", "John Doe"]
)
```

### Clean up memory
```python
close_pdf(document_id="doc1")  # Frees memory
```
