# PDF Redaction MCP Server

A Model Context Protocol (MCP) server that provides comprehensive PDF redaction capabilities using [FastMCP](https://github.com/jlowin/fastmcp) and [pymupdf](https://pymupdf.readthedocs.io/).

## Features

This MCP server enables LLMs to:

- **Extract text from PDFs** in multiple formats (plain text, JSON, or structured blocks)
- **Search for text patterns** using exact match or regex with location information
- **Redact text by search** - automatically find and redact all occurrences of specified strings
- **Redact by coordinates** - precisely redact specific areas of a PDF
- **Redact images** - remove images from PDFs with customisable overlays
- **Verify redactions** - confirm that sensitive information has been properly removed
- **Get PDF information** - retrieve metadata and structure information

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Using uv (Recommended)

```bash
# Clone or download the project
cd pdf-redaction-mcp

# Install dependencies
uv sync

# Run the server
uv run pdf-redaction-mcp
```

### Using pip

```bash
pip install -e .
pdf-redaction-mcp
```

## Usage

### Running the Server

The server supports multiple transport modes and configurations via command-line flags:

```bash
# Show all available options
uv run pdf-redaction-mcp --help

# STDIO mode (default) - for desktop clients
uv run pdf-redaction-mcp

# SSE mode - for mobile apps and remote clients
uv run pdf-redaction-mcp --transport sse --port 8000

# HTTP mode - for web-based clients  
uv run pdf-redaction-mcp --transport http --host 0.0.0.0 --port 8080

# With custom PDF directory (relative paths resolved against this)
uv run pdf-redaction-mcp --pdf-dir /path/to/pdfs

# Combined options
uv run pdf-redaction-mcp --transport sse --port 8000 --pdf-dir ~/Documents/pdfs
```

#### Command-Line Options

- `--transport {stdio,http,sse}`: Transport mode (default: stdio)
- `--host HOST`: Host to bind to for HTTP/SSE mode (default: 127.0.0.1)
- `--port PORT`: Port to listen on for HTTP/SSE mode (default: 8000)
- `--pdf-dir PDF_DIR`: Base directory for PDF files. Relative paths in tools will be resolved against this directory.

### Available Tools

The server provides **two sets of tools**:
1. **File-based tools** - For local files on disk (original tools)
2. **Base64 tools** - For uploaded PDFs in mobile/web apps (tools ending in `_base64`)

### When to Use Which?

**Use file-based tools when:**
- Working with PDFs already saved on your computer
- Using Claude Desktop with local files
- Running the server locally via STDIO

**Use base64 tools when:**
- Working with uploaded PDFs (mobile/web apps)
- Server deployed remotely (HTTP/SSE transport)
- No filesystem access available
- Processing PDFs in memory

---

### File-Based Tools (Local Files)

#### 1. `extract_text_from_pdf`

Extract text from a PDF for LLM consumption.

**Parameters:**
- `pdf_path` (str): Path to the PDF file
- `page_number` (int, optional): Specific page to extract (0-indexed)
- `format` (str): Output format - "text", "json", or "blocks"

**Example:**
```python
# Extract all text
extract_text_from_pdf(
    pdf_path="/path/to/document.pdf",
    format="text"
)

# Extract specific page as JSON
extract_text_from_pdf(
    pdf_path="/path/to/document.pdf",
    page_number=0,
    format="json"
)
```

#### 2. `search_text_in_pdf`

Search for text patterns and get their locations.

**Parameters:**
- `pdf_path` (str): Path to the PDF file
- `search_string` (str): Text or regex pattern to search for
- `case_sensitive` (bool): Whether search should be case sensitive
- `use_regex` (bool): Whether to treat search_string as regex
- `page_number` (int, optional): Specific page to search

**Example:**
```python
# Search for email addresses using regex
search_text_in_pdf(
    pdf_path="/path/to/document.pdf",
    search_string=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    use_regex=True
)
```

#### 3. `redact_text_by_search`

Automatically find and redact all occurrences of specified strings.

**Parameters:**
- `pdf_path` (str): Path to input PDF
- `output_path` (str): Path for redacted PDF
- `search_strings` (List[str]): List of strings to redact
- `case_sensitive` (bool): Whether search is case sensitive
- `fill_color` (Tuple[float, float, float]): RGB colour (0-1 range)
- `overlay_text` (str): Optional text over redacted area
- `text_color` (Tuple[float, float, float]): RGB colour for overlay text

**Example:**
```python
# Redact sensitive information
redact_text_by_search(
    pdf_path="/path/to/input.pdf",
    output_path="/path/to/redacted.pdf",
    search_strings=["CONFIDENTIAL", "john.doe@example.com", "123-45-6789"],
    fill_color=(0, 0, 0),  # Black
    overlay_text="[REDACTED]"
)
```

#### 4. `redact_by_coordinates`

Redact specific areas by their exact coordinates.

**Parameters:**
- `pdf_path` (str): Path to input PDF
- `output_path` (str): Path for redacted PDF
- `redactions` (List[Dict]): List of redaction areas with page, bbox, and optional text
- `fill_color` (Tuple[float, float, float]): RGB colour
- `overlay_text` (str): Default overlay text

**Example:**
```python
# Redact specific areas
redact_by_coordinates(
    pdf_path="/path/to/input.pdf",
    output_path="/path/to/redacted.pdf",
    redactions=[
        {"page": 0, "bbox": [100, 100, 300, 150], "text": "REDACTED"},
        {"page": 1, "bbox": [50, 200, 250, 250]}
    ],
    fill_color=(0, 0, 0)
)
```

#### 5. `redact_images_in_pdf`

Remove all images from specified pages.

**Parameters:**
- `pdf_path` (str): Path to input PDF
- `output_path` (str): Path for redacted PDF
- `page_numbers` (List[int], optional): Pages to process (all if None)
- `fill_color` (Tuple[float, float, float]): RGB colour
- `overlay_text` (str): Text over redacted images

**Example:**
```python
# Redact all images on first two pages
redact_images_in_pdf(
    pdf_path="/path/to/input.pdf",
    output_path="/path/to/no_images.pdf",
    page_numbers=[0, 1],
    overlay_text="[IMAGE REMOVED]"
)
```

#### 6. `verify_redactions`

Verify that redactions were applied correctly.

**Parameters:**
- `original_pdf` (str): Path to original PDF
- `redacted_pdf` (str): Path to redacted PDF
- `search_strings` (List[str], optional): Strings that should be gone

**Example:**
```python
# Verify sensitive data was removed
verify_redactions(
    original_pdf="/path/to/original.pdf",
    redacted_pdf="/path/to/redacted.pdf",
    search_strings=["CONFIDENTIAL", "secret@example.com"]
)
```

#### 7. `get_pdf_info`

Get metadata and structure information about a PDF.

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Example:**
```python
# Get PDF information
get_pdf_info(pdf_path="/path/to/document.pdf")
```

---

### Base64 Tools (Uploaded PDFs)

All base64 tools work identically to their file-based counterparts, but accept/return base64-encoded PDFs instead of file paths. Perfect for mobile apps and remote servers.

#### 1. `extract_text_from_pdf_base64`

Extract text from an uploaded PDF.

**Parameters:**
- `pdf_data` (str): Base64-encoded PDF
- `page_number` (int, optional): Specific page to extract
- `format` (str): Output format - "text", "json", or "blocks"

**Returns:** Extracted text (same as file-based version)

#### 2. `search_text_in_pdf_base64`

Search for text in an uploaded PDF.

**Parameters:**
- `pdf_data` (str): Base64-encoded PDF
- `search_string` (str): Text or regex pattern
- `case_sensitive` (bool): Case sensitivity
- `use_regex` (bool): Use regex
- `page_number` (int, optional): Specific page

**Returns:** JSON with matches and bounding boxes

#### 3. `redact_text_by_search_base64`

Redact text in an uploaded PDF.

**Parameters:**
- `pdf_data` (str): Base64-encoded PDF
- `search_strings` (List[str]): Strings to redact
- `case_sensitive` (bool): Case sensitivity
- `fill_color` (Tuple): RGB colour
- `overlay_text` (str): Overlay text
- `text_color` (Tuple): Text colour

**Returns:** JSON with `redacted_pdf` (base64) and summary

**Example workflow:**
```
User uploads PDF → Claude gets base64 → Calls redact_text_by_search_base64
→ Returns base64 redacted PDF → User downloads
```

#### 4. `redact_by_coordinates_base64`

Redact specific areas in an uploaded PDF.

**Parameters:**
- `pdf_data` (str): Base64-encoded PDF
- `redactions` (List[Dict]): Redaction areas
- `fill_color` (Tuple): RGB colour
- `overlay_text` (str): Overlay text

**Returns:** JSON with `redacted_pdf` (base64) and summary

#### 5. `redact_images_in_pdf_base64`

Remove images from an uploaded PDF.

**Parameters:**
- `pdf_data` (str): Base64-encoded PDF
- `page_numbers` (List[int], optional): Pages to process
- `fill_color` (Tuple): RGB colour
- `overlay_text` (str): Overlay text

**Returns:** JSON with `redacted_pdf` (base64) and summary

#### 6. `verify_redactions_base64`

Verify redactions in uploaded PDFs.

**Parameters:**
- `original_pdf_data` (str): Base64-encoded original PDF
- `redacted_pdf_data` (str): Base64-encoded redacted PDF
- `search_strings` (List[str], optional): Strings to check

**Returns:** JSON with verification results

#### 7. `get_pdf_info_base64`

Get metadata from an uploaded PDF.

**Parameters:**
- `pdf_data` (str): Base64-encoded PDF

**Returns:** JSON with PDF metadata and structure

---

## Configuration

This section covers how to configure the PDF Redaction MCP Server with various MCP clients.

**Quick Links:**
- [Claude Desktop](#claude-desktop) - Most common desktop setup
- [Cursor IDE](#cursor-ide) - For developers using Cursor
- [Cline (VSCode)](#cline-vscode-extension) - VSCode MCP extension
- [Other MCP Clients](#other-mcp-clients) - Generic STDIO configuration
- [Remote/Mobile Setup](#remote-server-httpsse---for-mobile-apps) - For mobile apps and web clients

---

### Claude Desktop

Add to your `claude_desktop_config.json`:

**Basic Configuration (STDIO mode):**

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp"
      ]
    }
  }
}
```

**With Custom PDF Directory:**

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp",
        "--pdf-dir",
        "/Users/yourname/Documents/PDFs"
      ]
    }
  }
}
```

This allows you to use relative paths like `"document.pdf"` instead of full paths.

### Cursor IDE

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp"
      ]
    }
  }
}
```

### Cline (VSCode Extension)

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp",
        "--pdf-dir",
        "${workspaceFolder}/pdfs"
      ]
    }
  }
}
```

### Other MCP Clients

For any MCP client supporting STDIO transport, use:

**Command:** `uv`

**Args:**
```
--directory /path/to/pdf-redaction-mcp
run
pdf-redaction-mcp
[optional flags like --pdf-dir]
```

### Remote Server (HTTP/SSE) - For Mobile Apps

Deploy the server remotely for use with Claude Android/iOS apps or web-based clients:

**1. Run the server in SSE mode:**

```bash
uv run pdf-redaction-mcp --transport sse --host 0.0.0.0 --port 8000
```

**2. Deploy to cloud with Docker:**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "pdf-redaction-mcp", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy to Railway, Fly.io, DigitalOcean, AWS, etc.

**3. Configure Claude Mobile App:**

In Claude Android/iOS app settings, add the remote MCP server:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "url": "https://your-domain.com/sse"
    }
  }
}
```

Now when users **upload PDFs** in the mobile app, Claude will automatically use the `_base64` tools!

### Environment Variables (Optional)

For production deployments, you can use environment variables:

```bash
# Set PDF directory via environment
export PDF_DIR=/var/pdfs

# Then reference in your startup script
uv run pdf-redaction-mcp --pdf-dir "$PDF_DIR"
```

### Real-World Configuration Examples

**Example 1: Personal Use with Claude Desktop**

Store all PDFs in your Documents folder:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/yourname/workspace/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp",
        "--pdf-dir",
        "/Users/yourname/Documents"
      ]
    }
  }
}
```

Now you can say: *"Redact emails from report.pdf"* instead of using full paths.

**Example 2: Team Deployment with Shared PDFs**

Deploy remotely with network-mounted PDF storage:

```bash
# On your server
uv run pdf-redaction-mcp \
  --transport sse \
  --host 0.0.0.0 \
  --port 8000 \
  --pdf-dir /mnt/shared-pdfs
```

Team members configure their clients to use the remote server.

**Example 3: Development Setup**

Use project-relative paths during development:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory",
        "${workspaceFolder}/pdf-redaction-mcp",
        "run",
        "pdf-redaction-mcp",
        "--pdf-dir",
        "${workspaceFolder}/test-pdfs"
      ]
    }
  }
}
```

---

## Workflow Examples

### Example 1: Redact Personal Information

**Without --pdf-dir flag:**
```
User: "Please redact all email addresses from /Users/john/Documents/reports/report.pdf"

LLM uses: redact_text_by_search(
  pdf_path="/Users/john/Documents/reports/report.pdf",
  output_path="/Users/john/Documents/reports/report_redacted.pdf",
  ...
)
```

**With --pdf-dir flag (configured as /Users/john/Documents/reports):**
```
User: "Please redact all email addresses from report.pdf"

LLM uses: redact_text_by_search(
  pdf_path="report.pdf",  # Automatically resolved to full path
  output_path="report_redacted.pdf",
  ...
)
```

**Workflow:**
```
1. User: "Please redact all email addresses and phone numbers from report.pdf"

2. LLM uses search_text_in_pdf to find patterns:
   - Email regex: \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b
   - Phone regex: \b\d{3}[-.]?\d{3}[-.]?\d{4}\b

3. LLM uses redact_text_by_search with found strings

4. LLM uses verify_redactions to confirm removal

5. LLM reports: "Successfully redacted 5 email addresses and 3 phone numbers"
```

### Example 2: Redact Specific Section

```
1. User: "Redact the financial table on page 3 of the report"

2. LLM uses extract_text_from_pdf with page_number=2, format="blocks"

3. LLM identifies table coordinates from block structure

4. LLM uses redact_by_coordinates with calculated bbox

5. LLM uses extract_text_from_pdf again to verify section is gone
```

### Example 3: Remove All Images

```
1. User: "Remove all images from the document but keep the text"

2. LLM uses get_pdf_info to see which pages have images

3. LLM uses redact_images_in_pdf on those pages

4. LLM verifies using get_pdf_info that images are gone
```

### Example 4: Mobile App with Uploaded PDF

```
1. User uploads confidential.pdf in Claude Android app

2. User: "Redact all email addresses and save the result"

3. LLM workflow:
   - Receives PDF as base64 automatically
   - search_text_in_pdf_base64(pdf_data, email_regex, use_regex=True)
   - redact_text_by_search_base64(pdf_data, found_emails)
   - verify_redactions_base64(original, redacted, found_emails)
   - Returns: {redacted_pdf: "base64...", total_redactions: 5}

4. Claude provides download link for redacted PDF

5. User downloads directly to device
```

---

---

## Troubleshooting

### Claude Desktop Connection Issues

**Problem:** MCP server not connecting in Claude Desktop

**Solutions:**
1. Verify the path in `claude_desktop_config.json` is correct:
   ```bash
   # Check if the directory exists
   ls -la /path/to/pdf-redaction-mcp
   ```

2. Test the server manually:
   ```bash
   cd /path/to/pdf-redaction-mcp
   uv run pdf-redaction-mcp --help
   ```

3. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.config/Claude/logs/`

### PDF Path Issues

**Problem:** "File not found" errors when using relative paths

**Solution:** Configure `--pdf-dir` flag in your MCP client config:
```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/pdf-redaction-mcp",
        "run", "pdf-redaction-mcp",
        "--pdf-dir", "/your/pdf/directory"
      ]
    }
  }
}
```

### Port Already in Use (HTTP/SSE mode)

**Problem:** `Address already in use` error when starting server

**Solution:** 
1. Use a different port:
   ```bash
   uv run pdf-redaction-mcp --transport sse --port 8001
   ```

2. Or find and kill the process using the port:
   ```bash
   # macOS/Linux
   lsof -ti:8000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

### UV Not Found

**Problem:** `uv: command not found`

**Solution:** Install UV package manager:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or use pip
pip install uv
```

---

## Development

### Running Tests

```bash
uv run pytest
```

### Project Structure

```
pdf-redaction-mcp/
├── src/
│   └── pdf_redaction_mcp/
│       ├── __init__.py
│       └── server.py          # Main MCP server implementation
├── tests/
│   └── test_server.py         # Unit tests
├── pyproject.toml             # Project dependencies
└── README.md                  # This file
```

## Technical Details

### Redaction Implementation

The server uses pymupdf's redaction annotations, which:

1. **Add redaction annotations** to mark areas for removal
2. **Apply redactions** to permanently remove content
3. **Cannot be undone** once saved - content is truly deleted from PDF structure

### Colour Format

Colours are specified as RGB tuples with values from 0 to 1:
- Black: `(0, 0, 0)`
- White: `(1, 1, 1)`
- Red: `(1, 0, 0)`
- Green: `(0, 1, 0)`
- Blue: `(0, 0, 1)`

### Coordinate System

PDF coordinates use bottom-left origin:
- `x0, y0`: Bottom-left corner of rectangle
- `x1, y1`: Top-right corner of rectangle

Bounding boxes: `[x0, y0, x1, y1]`

## Security Considerations

1. **Permanent Removal**: Redactions permanently remove content from PDF structure
2. **Verify Redactions**: Always use `verify_redactions` to confirm sensitive data is gone
3. **Backup Original**: Keep original files backed up before redacting
4. **File Paths**: Ensure proper file path validation in production
5. **Access Control**: Implement appropriate access controls for sensitive documents

## Limitations

- Only works with PDF files (use pymupdf's supported formats)
- Encrypted PDFs may require password authentication
- Very large PDFs may require significant memory
- Redactions are permanent once saved

## Contributing

Contributions are welcome! Please ensure:

1. Code follows existing style
2. Tests pass (`uv run pytest`)
3. Documentation is updated
4. Commit messages are clear

## Licence

MIT Licence - see LICENCE file for details

## Acknowledgements

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP framework
- [pymupdf](https://pymupdf.readthedocs.io/) - PDF manipulation library
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the [FastMCP documentation](https://github.com/jlowin/fastmcp)
- Check the [pymupdf documentation](https://pymupdf.readthedocs.io/)
