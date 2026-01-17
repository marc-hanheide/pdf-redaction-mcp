# PDF Redaction MCP Server - AI Coding Instructions

## Project Overview

A Model Context Protocol (MCP) server for PDF redaction using **FastMCP 2.x** and **pymupdf**. This server provides 7 tools for extracting, searching, and redacting text/images in PDFs with local files. Version 0.2.0.

## Architecture

All tools register to a single `mcp = FastMCP("PDF Redaction Server")` instance at module level ([server.py](src/pdf_redaction_mcp/server.py#L19)). Use `@mcp.tool()` decorator for all new tools.

### PDF Path Resolution

File-based tools use `resolve_pdf_path()` to handle relative paths:
- If `--pdf-dir` is set, relative paths are resolved against it
- Absolute paths are used as-is
- Global `PDF_BASE_DIR` variable stores the configured base directory

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
- Test error handling with non-existent files (should return JSON with `"error"` key)
- No real PDF fixtures currently - tests focus on error handling and structure

### Adding New Tools

All tools work with local PDF files only.

1. **Create the tool**:
   ```python
   @mcp.tool()
   def new_feature(pdf_path: str, ...) -> str:
       """Docstring explaining the tool."""
       try:
           pdf_path = resolve_pdf_path(pdf_path)  # Always resolve paths first
           doc = pymupdf.open(pdf_path)
           # ... implementation
           doc.close()
           return json.dumps(result)
       except Exception as e:
           return json.dumps({"error": str(e)})
   ```

2. **Always return JSON strings** for structured data or errors

3. **Add to README.md** in the Available Tools section

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

Always call `doc.close()` after pymupdf operations, even in error paths.

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

### Extract text with structure
```python
extract_text_from_pdf(pdf_path, format="blocks")  # Returns JSON with block-level info
```

### Search with regex
```python
search_text_in_pdf(pdf_path, search_string=r"\b\d{3}-\d{2}-\d{4}\b", use_regex=True)
```

### Redact by search (creates new file)
```python
redact_text_by_search(pdf_path, output_path, search_string, apply_immediately=True)
```

### Verify redactions worked
```python
verify_redactions(original_path, redacted_path, sensitive_terms=["SSN", "John Doe"])
```
