#!/usr/bin/env python3
"""Run the PDF Redaction MCP Server in HTTP/SSE mode for remote deployment.

This script starts the server in HTTP/SSE mode, suitable for:
- Claude Android/iOS apps
- Web-based clients
- Remote MCP connections

Usage:
    python run_server.py [--port PORT] [--host HOST]

Example:
    python run_server.py --port 8000 --host 0.0.0.0
"""

import argparse
from pdf_redaction_mcp.server import mcp


def main():
    parser = argparse.ArgumentParser(
        description="Run PDF Redaction MCP Server in HTTP/SSE mode"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting PDF Redaction MCP Server")
    print(f"Mode: HTTP/SSE (Server-Sent Events)")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"URL: http://{args.host}:{args.port}/mcp")
    print()
    print("Server features:")
    print("  • 7 file-based tools (for local files)")
    print("  • 7 base64 tools (for uploaded PDFs)")
    print("  • 14 tools total")
    print()
    print("Compatible with:")
    print("  • Claude Android app")
    print("  • Claude iOS app")
    print("  • Claude web app")
    print("  • Any MCP client with HTTP/SSE transport")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Run the server
    mcp.run(transport="sse", port=args.port, host=args.host)


if __name__ == "__main__":
    main()
