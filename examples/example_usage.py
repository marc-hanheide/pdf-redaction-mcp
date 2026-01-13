#!/usr/bin/env python3
"""Example usage of PDF Redaction MCP Server.

This script demonstrates how to use the MCP server tools programmatically.
"""

import json
from pdf_redaction_mcp.server import (
    extract_text_from_pdf,
    search_text_in_pdf,
    redact_text_by_search,
    redact_by_coordinates,
    redact_images_in_pdf,
    verify_redactions,
    get_pdf_info
)


def example_workflow():
    """Demonstrate a complete redaction workflow."""
    
    # Example PDF path (update with your actual PDF)
    pdf_path = "sample_document.pdf"
    output_path = "redacted_document.pdf"
    
    print("=== PDF Redaction Workflow Example ===\n")
    
    # Step 1: Get PDF information
    print("1. Getting PDF information...")
    info = get_pdf_info(pdf_path)
    info_dict = json.loads(info)
    if "error" in info_dict:
        print(f"Error: {info_dict['error']}")
        print("\nPlease provide a valid PDF file as 'sample_document.pdf'")
        return
    
    print(f"PDF has {info_dict['pages']} pages")
    print()
    
    # Step 2: Extract text to understand content
    print("2. Extracting text from first page...")
    text = extract_text_from_pdf(pdf_path, page_number=0, format="text")
    if isinstance(text, str) and not text.startswith('{"error"'):
        print(f"First 200 characters:\n{text[:200]}...")
    print()
    
    # Step 3: Search for specific patterns
    print("3. Searching for email addresses...")
    search_results = search_text_in_pdf(
        pdf_path=pdf_path,
        search_string=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        use_regex=True
    )
    search_dict = json.loads(search_results)
    print(f"Found {search_dict.get('total_matches', 0)} email addresses")
    print()
    
    # Step 4: Redact sensitive information
    print("4. Redacting sensitive information...")
    
    # Example: Redact specific words
    redaction_result = redact_text_by_search(
        pdf_path=pdf_path,
        output_path=output_path,
        search_strings=["CONFIDENTIAL", "SECRET"],
        fill_color=(0, 0, 0),
        overlay_text="[REDACTED]"
    )
    redact_dict = json.loads(redaction_result)
    print(f"Applied {redact_dict.get('total_redactions', 0)} redactions")
    print(f"Modified {redact_dict.get('pages_modified', 0)} pages")
    print()
    
    # Step 5: Verify redactions
    print("5. Verifying redactions...")
    verification = verify_redactions(
        original_pdf=pdf_path,
        redacted_pdf=output_path,
        search_strings=["CONFIDENTIAL", "SECRET"]
    )
    verify_dict = json.loads(verification)
    verdict = verify_dict.get("overall_verdict", {})
    print(f"Verification status: {verdict.get('status', 'UNKNOWN')}")
    print(f"Message: {verdict.get('message', 'No message')}")
    print()
    
    print("=== Workflow Complete ===")
    print(f"Redacted PDF saved to: {output_path}")


def example_coordinate_redaction():
    """Example of redacting specific areas by coordinates."""
    
    pdf_path = "sample_document.pdf"
    output_path = "coordinate_redacted.pdf"
    
    print("\n=== Coordinate-based Redaction Example ===\n")
    
    # Define specific areas to redact
    redactions = [
        {
            "page": 0,
            "bbox": [100, 100, 300, 150],
            "text": "REDACTED"
        },
        {
            "page": 0,
            "bbox": [100, 200, 300, 250],
            "text": "CONFIDENTIAL"
        }
    ]
    
    result = redact_by_coordinates(
        pdf_path=pdf_path,
        output_path=output_path,
        redactions=redactions,
        fill_color=(1, 0, 0)  # Red boxes
    )
    
    result_dict = json.loads(result)
    if "error" not in result_dict:
        print(f"Applied {result_dict.get('total_redactions', 0)} coordinate-based redactions")
        print(f"Output saved to: {output_path}")
    else:
        print(f"Error: {result_dict['error']}")


def example_image_redaction():
    """Example of removing all images from a PDF."""
    
    pdf_path = "sample_document.pdf"
    output_path = "no_images.pdf"
    
    print("\n=== Image Redaction Example ===\n")
    
    result = redact_images_in_pdf(
        pdf_path=pdf_path,
        output_path=output_path,
        overlay_text="[IMAGE REMOVED FOR PRIVACY]"
    )
    
    result_dict = json.loads(result)
    if "error" not in result_dict:
        print(f"Removed {result_dict.get('total_images_redacted', 0)} images")
        print(f"Processed {result_dict.get('pages_processed', 0)} pages")
        print(f"Output saved to: {output_path}")
    else:
        print(f"Error: {result_dict['error']}")


if __name__ == "__main__":
    print("PDF Redaction MCP Server - Example Usage\n")
    print("=" * 50)
    
    # Run the main workflow example
    example_workflow()
    
    # Uncomment to try other examples:
    # example_coordinate_redaction()
    # example_image_redaction()
