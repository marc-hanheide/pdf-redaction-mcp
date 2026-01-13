"""PDF Redaction MCP Server.

This package provides an MCP server for PDF redaction operations using pymupdf.
"""

from .server import mcp, main

__version__ = "0.1.0"
__all__ = ["mcp", "main"]
