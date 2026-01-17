# PDF Redaction MCP Server - Project Overview

## Summary

A production-ready Model Context Protocol (MCP) server for comprehensive PDF redaction operations, built with FastMCP2 and pymupdf. Supports local PDF files for seamless integration with desktop applications.

## Project Information

- **Name**: pdf-redaction-mcp
- **Version**: 0.2.0
- **Language**: Python 3.10+
- **Framework**: FastMCP 2.x
- **PDF Library**: pymupdf 1.24+
- **Package Manager**: UV
- **License**: MIT
- **Total Tools**: 7 (for local PDF files)

## Features

### Core Capabilities

1. **Text Extraction**
   - Multiple formats (plain text, JSON, structured blocks)
   - Page-specific or full document extraction
   - Preserves text structure and layout information
   - Works with local PDF files

2. **Text Search**
   - Exact string matching
   - Regular expression support
   - Case-sensitive/insensitive options
   - Returns bounding box coordinates
   - Works with local PDF files

3. **Text Redaction**
   - Search-based automatic redaction
   - Coordinate-based precise redaction
   - Customisable colours and overlay text
   - Batch processing across multiple pages
   - Works with local PDF files

4. **Image Redaction**
   - Complete image removal
   - Page-specific or document-wide
   - Customisable replacement text
   - Works with local PDF files

5. **Verification**
   - Confirm redactions were applied
   - Compare original vs redacted
   - Search for remaining sensitive data
   - Word count analysis
   - Works with local PDF files

6. **PDF Information**
   - Metadata extraction
   - Page structure analysis
   - Image and link counting
   - Works with local PDF files

### Deployment Modes

**Local (STDIO) - Claude Desktop/Cursor:**
- File-based tools for local PDFs
- Direct filesystem access
- Traditional MCP integration

**Remote (HTTP/SSE) - Remote Servers:**
- Same file-based tools accessible remotely
- Network-based access to local PDFs
- Cloud deployment support

### Technical Features

- **File-Based Tools**: Works with local PDF files
- **Error Handling**: Comprehensive JSON-based error reporting
- **Type Safety**: Full type hints throughout
- **Multiple Transports**: STDIO (default) and HTTP/SSE
- **MCP Standard**: Fully compliant with MCP specification
- **Testing**: Complete test suite with pytest
- **Documentation**: Extensive docs with examples

## Project Structure

```
pdf-redaction-mcp/
├── src/
│   └── pdf_redaction_mcp/
│       ├── __init__.py           # Package initialisation
│       └── server.py             # Main MCP server (700+ lines)
├── tests/
│   └── test_server.py            # Unit tests
├── examples/
│   └── example_usage.py          # Usage examples
├── pyproject.toml                # Project configuration
├── README.md                     # Comprehensive documentation
├── QUICKSTART.md                 # Quick start guide
├── CHANGELOG.md                  # Version history
├── LICENSE                       # MIT License
└── .gitignore                    # Git ignore rules
```

## Available Tools

The server provides **7 tools** for working with local PDF files:

### 1. extract_text_from_pdf
Extract text from PDF files in multiple formats.

**Use cases:**
- Converting PDFs to machine-readable text
- Analysing PDF content before redaction
- Extracting specific pages

### 2. search_text_in_pdf
Search for text patterns with location data.

**Use cases:**
- Finding all email addresses
- Locating phone numbers
- Identifying sensitive terms
- Regex pattern matching

### 3. redact_text_by_search
Automatically redact all occurrences of text.

**Use cases:**
- Removing personal information
- Redacting confidential terms
- Bulk redaction of patterns
- Compliance with data protection

### 4. redact_by_coordinates
Precisely redact specific areas.

**Use cases:**
- Redacting specific tables
- Removing signature blocks
- Targeted section removal
- Layout-aware redaction

### 5. redact_images_in_pdf
Remove images from PDFs.

**Use cases:**
- Privacy protection
- Reducing file size
- Removing logos/photos
- Compliance with image restrictions

### 6. verify_redactions
Confirm redactions were successful.

**Use cases:**
- Quality assurance
- Compliance verification
- Testing redaction workflows
- Audit trails

### 7. get_pdf_info
Extract PDF metadata and structure.

**Use cases:**
- Understanding PDF layout
- Planning redaction strategy
- File analysis
- Debugging

---

## Integration Examples

### With Claude Desktop

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

### With Cursor IDE

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

### Programmatic Usage

```python
from pdf_redaction_mcp.server import redact_text_by_search
import json

result = redact_text_by_search.fn(
    pdf_path="input.pdf",
    output_path="redacted.pdf",
    search_strings=["CONFIDENTIAL", "SECRET"],
    fill_color=(0, 0, 0)
)

print(json.dumps(json.loads(result), indent=2))
```

## Workflow Examples

### Example 1: Automated PII Removal

```
User: "Remove all personal information from contract.pdf"

LLM workflow:
1. extract_text_from_pdf(contract.pdf) - analyse content
2. search_text_in_pdf(..., regex for emails)
3. search_text_in_pdf(..., regex for phones)
4. redact_text_by_search(..., found patterns)
5. verify_redactions(..., confirm removal)
6. Report: "Redacted 3 emails, 2 phone numbers"
```

### Example 2: Section Redaction

```
User: "Redact the financial table on page 5"

LLM workflow:
1. extract_text_from_pdf(..., page=4, format="blocks")
2. Identify table coordinates from structure
3. redact_by_coordinates(..., calculated bbox)
4. extract_text_from_pdf(..., verify removal)
```

### Example 3: Image Privacy

```
User: "Remove all photos from the document"

LLM workflow:
1. get_pdf_info(...) - identify pages with images
2. redact_images_in_pdf(..., all pages)
3. get_pdf_info(...) - verify images removed
4. Report: "Removed 12 images across 8 pages"
```

## Installation & Testing

### Quick Install
```bash
cd pdf-redaction-mcp
uv sync
```

### Run Tests
```bash
uv run pytest -v
```

### Start Server
```bash
uv run pdf-redaction-mcp
```

## Security Considerations

1. **Irreversible Operations**: Redactions permanently remove content
2. **Always Verify**: Use verify_redactions after redaction
3. **Backup Originals**: Keep unredacted versions secure
4. **File Paths**: Validate paths to prevent unauthorised access
5. **Encrypted PDFs**: May require passwords for processing

## Performance

- **Small PDFs** (<10 pages): Near-instant processing
- **Medium PDFs** (10-100 pages): Seconds
- **Large PDFs** (100+ pages): May require minutes
- **Memory**: Scales with PDF size and image count

## Limitations

1. Only processes PDF files
2. Encrypted PDFs require authentication
3. Large PDFs may need significant memory
4. Redactions are permanent after saving
5. Some complex PDF structures may need special handling

## Dependencies

### Core
- fastmcp >= 2.0.0
- pymupdf >= 1.24.0

### Development
- pytest >= 8.0.0
- pytest-asyncio >= 0.23.0

## Future Enhancements

Potential additions for future versions:
- OCR support for scanned documents
- Batch processing of multiple PDFs
- Custom redaction patterns
- Watermarking capabilities
- PDF compression options
- Form field redaction
- Metadata scrubbing
- CLI interface
- Web interface

## Support & Resources

- **Documentation**: README.md, QUICKSTART.md
- **Examples**: examples/example_usage.py
- **Tests**: tests/test_server.py
- **FastMCP**: https://github.com/jlowin/fastmcp
- **pymupdf**: https://pymupdf.readthedocs.io/

## Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages

## License

MIT License - see LICENSE file for details.

---

**Built by**: Marc Hanheide
**Framework**: FastMCP 2.x by @jlowin
**PDF Processing**: pymupdf by Artifex
**Date**: January 2025
