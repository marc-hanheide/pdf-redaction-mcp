#!/usr/bin/env python3
"""Example usage of PDF Redaction MCP Server.

This script demonstrates how to use the MCP server tools programmatically
with the new session-based in-memory workflow.
"""

import json
from pdf_redaction_mcp.server import (
    load_pdf,
    save_pdf,
    close_pdf,
    list_loaded_pdfs,
    extract_text_from_pdf,
    search_text_in_pdf,
    redact_text_by_search,
    redact_by_coordinates,
    redact_images_in_pdf,
    verify_redactions,
    get_pdf_info
)


def example_workflow():
    """Demonstrate a complete redaction workflow using session-based approach."""
    
    # Example PDF path (update with your actual PDF)
    pdf_path = "sample_document.pdf"
    output_path = "redacted_document.pdf"
    
    print("=== PDF Redaction Workflow Example ===\n")
    
    # Step 1: Load PDF into memory
    print("1. Loading PDF into memory...")
    load_result = load_pdf(pdf_path, document_id="sample")
    load_dict = json.loads(load_result)
    if "error" in load_dict:
        print(f"Error: {load_dict['error']}")
        print("\nPlease provide a valid PDF file as 'sample_document.pdf'")
        return
    
    print(f"Loaded document '{load_dict['document_id']}' with {load_dict['pages']} pages")
    print()
    
    # Step 2: Get PDF information
    print("2. Getting PDF information...")
    info = get_pdf_info("sample")
    info_dict = json.loads(info)
    print(f"PDF has {info_dict['pages']} pages")
    print()
    
    # Step 3: Extract text to understand content
    print("3. Extracting text from first page...")
    text = extract_text_from_pdf("sample", page_number=0, format="text")
    if isinstance(text, str) and not text.startswith('{"error"'):
        print(f"First 200 characters:\n{text[:200]}...")
    print()
    
    # Step 4: Search for specific patterns
    print("4. Searching for email addresses...")
    search_results = search_text_in_pdf(
        document_id="sample",
        search_string=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        use_regex=True
    )
    search_dict = json.loads(search_results)
    print(f"Found {search_dict.get('total_matches', 0)} email addresses")
    print()
    
    # Step 5: Redact sensitive information (in-memory)
    print("5. Redacting sensitive information...")
    
    # Example: Redact specific words
    redaction_result = redact_text_by_search(
        document_id="sample",
        search_strings=["CONFIDENTIAL", "SECRET"],
        fill_color=(0, 0, 0),
        overlay_text="[REDACTED]"
    )
    redact_dict = json.loads(redaction_result)
    print(f"Applied {redact_dict.get('total_redactions', 0)} redactions")
    print(f"Modified {redact_dict.get('pages_modified', 0)} pages")
    print()
    
    # Step 6: Save the redacted document
    print("6. Saving redacted document...")
    save_result = save_pdf("sample", output_path)
    save_dict = json.loads(save_result)
    print(f"Saved to: {save_dict.get('output_path', output_path)}")
    print()
    
    # Step 7: Load both documents for verification
    print("7. Verifying redactions...")
    load_pdf(output_path, document_id="redacted")
    
    verification = verify_redactions(
        original_document_id="sample",
        redacted_document_id="redacted",
        search_strings=["CONFIDENTIAL", "SECRET"]
    )
    verify_dict = json.loads(verification)
    verdict = verify_dict.get("overall_verdict", {})
    print(f"Verification status: {verdict.get('status', 'UNKNOWN')}")
    print(f"Message: {verdict.get('message', 'No message')}")
    print()
    
    # Step 8: Clean up
    print("8. Cleaning up memory...")
    close_pdf("sample")
    close_pdf("redacted")
    print()
    
    print("=== Workflow Complete ===")
    print(f"Redacted PDF saved to: {output_path}")


def example_coordinate_redaction():
    """Example of redacting specific areas by coordinates using session-based approach."""
    
    pdf_path = "sample_document.pdf"
    output_path = "coordinate_redacted.pdf"
    
    print("\n=== Coordinate-based Redaction Example ===\n")
    
    # Load PDF
    print("Loading PDF...")
    load_result = load_pdf(pdf_path, document_id="coord_sample")
    if "error" in json.loads(load_result):
        print(f"Error loading PDF: {json.loads(load_result)['error']}")
        return
    
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
        document_id="coord_sample",
        redactions=redactions,
        fill_color=(1, 0, 0)  # Red boxes
    )
    
    result_dict = json.loads(result)
    if "error" not in result_dict:
        print(f"Applied {result_dict.get('total_redactions', 0)} coordinate-based redactions")
        
        # Save the result
        save_pdf("coord_sample", output_path)
        print(f"Output saved to: {output_path}")
        
        # Clean up
        close_pdf("coord_sample")
    else:
        print(f"Error: {result_dict['error']}")


def example_image_redaction():
    """Example of removing all images from a PDF using session-based approach."""
    
    pdf_path = "sample_document.pdf"
    output_path = "no_images.pdf"
    
    print("\n=== Image Redaction Example ===\n")
    
    # Load PDF
    print("Loading PDF...")
    load_result = load_pdf(pdf_path, document_id="img_sample")
    if "error" in json.loads(load_result):
        print(f"Error loading PDF: {json.loads(load_result)['error']}")
        return
    
    result = redact_images_in_pdf(
        document_id="img_sample",
        overlay_text="[IMAGE REMOVED FOR PRIVACY]"
    )
    
    result_dict = json.loads(result)
    if "error" not in result_dict:
        print(f"Removed {result_dict.get('total_images_redacted', 0)} images")
        print(f"Processed {result_dict.get('pages_processed', 0)} pages")
        
        # Save the result
        save_pdf("img_sample", output_path)
        print(f"Output saved to: {output_path}")
        
        # Clean up
        close_pdf("img_sample")
    else:
        print(f"Error: {result_dict['error']}")


def example_list_documents():
    """Example of listing currently loaded documents."""
    
    print("\n=== List Loaded Documents Example ===\n")
    
    # Load some documents
    load_pdf("sample_document.pdf", document_id="doc1")
    load_pdf("sample_document.pdf", document_id="doc2")
    
    # List all loaded documents
    result = list_loaded_pdfs()
    result_dict = json.loads(result)
    
    print(f"Total documents loaded: {result_dict.get('total_documents', 0)}")
    for doc in result_dict.get('documents', []):
        print(f"  - {doc['document_id']}: {doc['pages']} pages")
    
    # Clean up
    close_pdf("doc1")
    close_pdf("doc2")


if __name__ == "__main__":
    print("PDF Redaction MCP Server - Example Usage\n")
    print("Session-based in-memory workflow demonstration")
    print("=" * 50)
    
    # Run the main workflow example
    example_workflow()
    
    # Uncomment to try other examples:
    # example_coordinate_redaction()
    # example_image_redaction()
    # example_list_documents()
