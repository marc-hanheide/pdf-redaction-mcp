#!/usr/bin/env python3
"""Example usage of PDF Redaction MCP Server with Base64 tools.

This script demonstrates how to use the base64 tools for working with
uploaded PDFs (as would happen in mobile/web apps).
"""

import json
import base64
from pathlib import Path
from pdf_redaction_mcp.server import (
    extract_text_from_pdf_base64,
    search_text_in_pdf_base64,
    redact_text_by_search_base64,
    verify_redactions_base64,
    get_pdf_info_base64
)


def load_pdf_as_base64(pdf_path: str) -> str:
    """Load a PDF file and encode it as base64."""
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    return base64.b64encode(pdf_bytes).decode('utf-8')


def save_base64_as_pdf(base64_data: str, output_path: str):
    """Save base64-encoded PDF to a file."""
    pdf_bytes = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)


def example_mobile_workflow():
    """Simulate a mobile app workflow with uploaded PDF."""
    
    # Simulate user uploading a PDF in mobile app
    pdf_path = "sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: Please provide a PDF file as '{pdf_path}'")
        print("This example simulates how mobile apps work with uploaded PDFs.")
        return
    
    print("=== Mobile App Workflow Simulation ===\n")
    print("Simulating: User uploads PDF in Claude Android app\n")
    
    # Step 1: Convert uploaded PDF to base64 (happens automatically in real apps)
    print("1. Converting PDF to base64 (automatic in mobile apps)...")
    pdf_base64 = load_pdf_as_base64(pdf_path)
    print(f"   PDF encoded: {len(pdf_base64)} characters")
    print()
    
    # Step 2: Get PDF info
    print("2. Analysing uploaded PDF...")
    info_result = get_pdf_info_base64.fn(pdf_base64)
    info = json.loads(info_result)
    
    if "error" in info:
        print(f"Error: {info['error']}")
        return
    
    print(f"   Pages: {info['pages']}")
    print(f"   Images: {sum(p['image_count'] for p in info['page_info'])}")
    print()
    
    # Step 3: Extract and display some text
    print("3. Extracting text from first page...")
    text_result = extract_text_from_pdf_base64.fn(
        pdf_data=pdf_base64,
        page_number=0,
        format="text"
    )
    if not text_result.startswith('{"error"'):
        print(f"   Preview: {text_result[:150]}...")
    print()
    
    # Step 4: Search for sensitive patterns
    print("4. Searching for email addresses...")
    search_result = search_text_in_pdf_base64.fn(
        pdf_data=pdf_base64,
        search_string=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        use_regex=True
    )
    search_data = json.loads(search_result)
    print(f"   Found: {search_data.get('total_matches', 0)} email addresses")
    print()
    
    # Step 5: Redact sensitive information
    print("5. Redacting sensitive information...")
    
    # Example: Redact all instances of "CONFIDENTIAL"
    redact_result = redact_text_by_search_base64.fn(
        pdf_data=pdf_base64,
        search_strings=["CONFIDENTIAL", "SECRET"],
        fill_color=(0, 0, 0),
        overlay_text="[REDACTED]"
    )
    
    redact_data = json.loads(redact_result)
    
    if "error" in redact_data:
        print(f"   Error: {redact_data['error']}")
        return
    
    print(f"   Redactions applied: {redact_data.get('total_redactions', 0)}")
    print(f"   Pages modified: {redact_data.get('pages_modified', 0)}")
    print()
    
    # Step 6: Save the redacted PDF (in real app, this would be a download link)
    print("6. Saving redacted PDF...")
    redacted_pdf_base64 = redact_data.get('redacted_pdf')
    
    if redacted_pdf_base64:
        output_path = "redacted_mobile_example.pdf"
        save_base64_as_pdf(redacted_pdf_base64, output_path)
        print(f"   Saved to: {output_path}")
        print("   (In mobile app, user would get a download link)")
    print()
    
    # Step 7: Verify redactions
    print("7. Verifying redactions...")
    verify_result = verify_redactions_base64.fn(
        original_pdf_data=pdf_base64,
        redacted_pdf_data=redacted_pdf_base64,
        search_strings=["CONFIDENTIAL", "SECRET"]
    )
    
    verify_data = json.loads(verify_result)
    verdict = verify_data.get("overall_verdict", {})
    
    print(f"   Status: {verdict.get('status', 'UNKNOWN')}")
    print(f"   Message: {verdict.get('message', 'No message')}")
    print()
    
    print("=== Workflow Complete ===")
    print("\nThis is exactly how it works in Claude mobile apps:")
    print("1. User uploads PDF → Automatically converted to base64")
    print("2. Claude calls MCP tools with base64 data")
    print("3. Server processes in memory (no files written)")
    print("4. Returns base64 result")
    print("5. User downloads redacted PDF")


def example_compare_approaches():
    """Compare file-based vs base64 approaches."""
    
    print("\n=== Comparing File-Based vs Base64 Approaches ===\n")
    
    print("FILE-BASED TOOLS:")
    print("  • Input: File path string")
    print("  • Output: File path string (saves to disk)")
    print("  • Use case: Local files, Claude Desktop")
    print("  • Example: extract_text_from_pdf('/path/to/file.pdf')")
    print()
    
    print("BASE64 TOOLS:")
    print("  • Input: Base64-encoded PDF string")
    print("  • Output: Base64-encoded PDF in JSON")
    print("  • Use case: Uploaded PDFs, mobile apps, remote servers")
    print("  • Example: extract_text_from_pdf_base64(base64_string)")
    print()
    
    print("WHEN TO USE WHICH:")
    print("  ✓ Local computer + existing files = File-based tools")
    print("  ✓ Mobile app + uploaded PDF = Base64 tools")
    print("  ✓ Remote server deployment = Base64 tools")
    print("  ✓ No filesystem access = Base64 tools")


if __name__ == "__main__":
    print("PDF Redaction MCP Server - Base64 Tools Example\n")
    print("=" * 60)
    
    # Run the mobile workflow simulation
    example_mobile_workflow()
    
    # Show comparison
    example_compare_approaches()
    
    print("\n" + "=" * 60)
    print("\nFor remote deployment, see README.md section:")
    print("'Remote Server (HTTP/SSE) - For Mobile Apps'")
