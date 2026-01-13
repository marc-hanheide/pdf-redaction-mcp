# Quick Start Guide

Get up and running with the PDF Redaction MCP Server in minutes.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- A PDF file to test with

## Installation

1. Clone or download this repository:
```bash
cd pdf-redaction-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Test the installation:
```bash
uv run pytest
```

All tests should pass.

## Running the Server

### For Claude Desktop / Cursor (STDIO Mode)

Run the server in STDIO mode:
```bash
uv run pdf-redaction-mcp
```

The server will start and wait for JSON-RPC messages over STDIO.

### Testing with MCP Inspector

FastMCP includes a built-in inspector for testing:

```bash
# Start the server in HTTP mode for inspection
uv run python -c "from pdf_redaction_mcp.server import mcp; mcp.run(transport='sse')"
```

Then in another terminal:
```bash
# Install MCP CLI tools if needed
uv add --dev mcp[cli]

# Run inspector
uv run mcp inspect http://localhost:8000/mcp
```

## Quick Test

Create a simple test PDF and try the tools:

```python
# test_quick.py
from pdf_redaction_mcp.server import get_pdf_info
import json

# Test with any PDF file
result = get_pdf_info.fn("your_file.pdf")
info = json.loads(result)
print(json.dumps(info, indent=2))
```

Run it:
```bash
uv run python test_quick.py
```

## Integration with Claude Desktop

1. Find your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the server configuration:
```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "/full/path/to/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp"
      ]
    }
  }
}
```

3. Restart Claude Desktop

4. In a new conversation, you can now ask Claude to:
   - "Extract text from this PDF: /path/to/file.pdf"
   - "Redact all email addresses in /path/to/file.pdf"
   - "Remove all images from /path/to/file.pdf"

## Common Use Cases

### Redact Personal Information

"Please redact all email addresses and phone numbers from /path/to/document.pdf and save to /path/to/redacted.pdf"

Claude will:
1. Search for email patterns
2. Search for phone number patterns
3. Apply redactions
4. Verify the redactions worked

### Redact Specific Words

"Redact the word 'CONFIDENTIAL' from all pages of /path/to/document.pdf"

### Remove Sensitive Images

"Remove all images from /path/to/document.pdf but keep the text"

### Verify Redactions

"Check if 'secret@company.com' still appears in /path/to/redacted.pdf"

## Troubleshooting

### Server doesn't start
- Ensure Python 3.10+ is installed: `python --version`
- Reinstall dependencies: `uv sync --reinstall`
- Check for errors: `uv run pytest -v`

### PDF operations fail
- Ensure the PDF file exists and is readable
- Check if the PDF is encrypted (may need password)
- Verify sufficient disk space for output files

### Claude Desktop integration issues
- Verify the path in `claude_desktop_config.json` is absolute
- Check Claude Desktop logs for errors
- Restart Claude Desktop completely

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Check [examples/example_usage.py](examples/example_usage.py) for programmatic usage
- Explore the [test suite](tests/) for more examples

## Getting Help

- Check [pymupdf documentation](https://pymupdf.readthedocs.io/)
- Review [FastMCP documentation](https://github.com/jlowin/fastmcp)
- Open an issue on GitHub
