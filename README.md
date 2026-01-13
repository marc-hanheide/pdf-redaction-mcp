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

The server can be run in different transport modes:

#### STDIO (Default - for Claude Desktop, Cursor, etc.)

```bash
uv run pdf-redaction-mcp
```

#### HTTP/SSE (for web-based clients)

```python
from pdf_redaction_mcp.server import mcp

# Run as HTTP server
mcp.run(transport="sse")
```

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

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": ["run", "pdf-redaction-mcp"],
      "cwd": "/path/to/pdf-redaction-mcp"
    }
  }
}
```

### Cursor IDE

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "command": "uv",
      "args": ["run", "pdf-redaction-mcp"],
      "cwd": "/path/to/pdf-redaction-mcp"
    }
  }
}
```

### Remote Server (HTTP/SSE) - For Mobile Apps

Deploy the server remotely for use with Claude Android/iOS apps:

**1. Run the server in HTTP/SSE mode:**

```python
# Create a file: run_server.py
from pdf_redaction_mcp.server import mcp

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)
```

**2. Deploy to cloud:**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "python", "run_server.py"]
```

Deploy to Railway, Fly.io, DigitalOcean, AWS, etc.

**3. Configure Claude Mobile App:**

In Claude Android/iOS app settings:

```json
{
  "mcpServers": {
    "pdf-redaction": {
      "url": "https://your-domain.com/mcp"
    }
  }
}
```

Now when users **upload PDFs** in the mobile app, Claude will automatically use the `_base64` tools!

---

## Workflow Examples

### Example 1: Redact Personal Information

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
