"""PDF Redaction MCP Server using FastMCP and pymupdf.

This MCP server provides tools for:
- Converting PDFs to text
- Searching for text patterns in PDFs
- Redacting text by search string or coordinates
- Redacting images
- Verifying redactions
"""

import warnings
import pymupdf
import re
import json
import base64
import io
import uvicorn
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware


# Suppress known pymupdf SWIG deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*", message=".*swigvarlink.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*", message=".*SwigPyPacked.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*", message=".*SwigPyObject.*")

# Create the MCP server instance
mcp = FastMCP("PDF Redaction Server")

# Global configuration for PDF base directory
PDF_BASE_DIR: Optional[Path] = None


def resolve_pdf_path(pdf_path: str) -> str:
    """Resolve PDF path using the configured base directory if path is relative.
    
    Args:
        pdf_path: Path to PDF file (absolute or relative)
        
    Returns:
        Resolved absolute path
    """
    path = Path(pdf_path)
    if PDF_BASE_DIR and not path.is_absolute():
        return str(PDF_BASE_DIR / path)
    return pdf_path


@mcp.tool()
def extract_text_from_pdf(
    pdf_path: str,
    page_number: Optional[int] = None,
    format: str = "text"
) -> str:
    """Extract text from a PDF file for LLM consumption.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: Specific page number to extract (0-indexed). If None, extracts all pages
        format: Output format - "text" (plain text), "json" (structured), or "blocks" (text blocks)
    
    Returns:
        Extracted text content in the specified format
    """
    try:
        pdf_path = resolve_pdf_path(pdf_path)
        doc = pymupdf.open(pdf_path)
        
        if page_number is not None:
            if page_number < 0 or page_number >= len(doc):
                doc.close()
                return json.dumps({"error": f"Invalid page number. PDF has {len(doc)} pages"})
            pages_to_process = [page_number]
        else:
            pages_to_process = range(len(doc))
        
        if format == "json":
            result = {
                "total_pages": len(doc),
                "pages": []
            }
            
            for page_num in pages_to_process:
                page = doc[page_num]
                result["pages"].append({
                    "page_number": page_num,
                    "text": page.get_text("text"),
                    "word_count": len(page.get_text("text").split())
                })
            
            doc.close()
            return json.dumps(result, indent=2)
        
        elif format == "blocks":
            result = {
                "total_pages": len(doc),
                "pages": []
            }
            
            for page_num in pages_to_process:
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                result["pages"].append({
                    "page_number": page_num,
                    "blocks": blocks
                })
            
            doc.close()
            return json.dumps(result, indent=2)
        
        else:  # plain text
            text_parts = []
            for page_num in pages_to_process:
                page = doc[page_num]
                text_parts.append(f"=== Page {page_num + 1} ===\n{page.get_text('text')}\n")
            
            doc.close()
            return "\n".join(text_parts)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_text_in_pdf(
    pdf_path: str,
    search_string: str,
    case_sensitive: bool = False,
    use_regex: bool = False,
    page_number: Optional[int] = None
) -> str:
    """Search for text in a PDF and return all occurrences with their locations.
    
    Args:
        pdf_path: Path to the PDF file
        search_string: Text or regex pattern to search for
        case_sensitive: Whether search should be case sensitive
        use_regex: Whether to treat search_string as a regex pattern
        page_number: Specific page to search (0-indexed). If None, searches all pages
    
    Returns:
        JSON string containing all matches with page numbers and bounding boxes
    """
    try:
        pdf_path = resolve_pdf_path(pdf_path)
        doc = pymupdf.open(pdf_path)
        matches = []
        
        pages_to_search = [page_number] if page_number is not None else range(len(doc))
        
        for page_num in pages_to_search:
            page = doc[page_num]
            
            if use_regex:
                # Extract text and search with regex
                text = page.get_text("text")
                flags = 0 if case_sensitive else re.IGNORECASE
                regex_matches = re.finditer(search_string, text, flags)
                
                for match in regex_matches:
                    # Find the bounding box for this text
                    rects = page.search_for(match.group())
                    for rect in rects:
                        matches.append({
                            "page": page_num,
                            "text": match.group(),
                            "bbox": list(rect),
                            "match_type": "regex"
                        })
            else:
                # Use pymupdf's built-in search
                flags = 0
                if not case_sensitive:
                    flags |= pymupdf.TEXT_PRESERVE_WHITESPACE
                
                rects = page.search_for(search_string)
                for rect in rects:
                    matches.append({
                        "page": page_num,
                        "text": search_string,
                        "bbox": list(rect),
                        "match_type": "exact"
                    })
        
        doc.close()
        
        result = {
            "search_string": search_string,
            "total_matches": len(matches),
            "matches": matches
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redact_text_by_search(
    pdf_path: str,
    output_path: str,
    search_strings: List[str],
    case_sensitive: bool = False,
    fill_color: Tuple[float, float, float] = (0, 0, 0),
    overlay_text: str = "",
    text_color: Tuple[float, float, float] = (1, 1, 1)
) -> str:
    """Redact all occurrences of specified text strings in a PDF.
    
    Args:
        pdf_path: Path to the input PDF file
        output_path: Path where the redacted PDF will be saved
        search_strings: List of strings to search for and redact
        case_sensitive: Whether search should be case sensitive
        fill_color: RGB color for redaction box (0-1 range). Default is black (0,0,0)
        overlay_text: Optional text to display over redacted area
        text_color: RGB color for overlay text (0-1 range). Default is white (1,1,1)
    
    Returns:
        JSON string with summary of redactions applied
    """
    try:
        pdf_path = resolve_pdf_path(pdf_path)
        output_path = resolve_pdf_path(output_path)
        doc = pymupdf.open(pdf_path)
        total_redactions = 0
        redaction_summary = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_redactions = 0
            
            for search_string in search_strings:
                # Search for all occurrences
                rects = page.search_for(search_string)
                
                for rect in rects:
                    # Add redaction annotation
                    page.add_redact_annot(
                        rect,
                        text=overlay_text,
                        fill=fill_color,
                        text_color=text_color
                    )
                    page_redactions += 1
                    total_redactions += 1
            
            if page_redactions > 0:
                # Apply all redactions on this page
                page.apply_redactions()
                redaction_summary.append({
                    "page": page_num,
                    "redactions": page_redactions
                })
        
        # Save the redacted document
        doc.save(output_path)
        doc.close()
        
        result = {
            "input_file": pdf_path,
            "output_file": output_path,
            "total_redactions": total_redactions,
            "pages_modified": len(redaction_summary),
            "summary": redaction_summary,
            "search_strings": search_strings
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redact_by_coordinates(
    pdf_path: str,
    output_path: str,
    redactions: List[Dict[str, Any]],
    fill_color: Tuple[float, float, float] = (0, 0, 0),
    overlay_text: str = ""
) -> str:
    """Redact specific areas of a PDF by coordinates.
    
    Args:
        pdf_path: Path to the input PDF file
        output_path: Path where the redacted PDF will be saved
        redactions: List of redaction areas, each with:
            - page: Page number (0-indexed)
            - bbox: Bounding box as [x0, y0, x1, y1]
            - text: Optional overlay text for this specific redaction
        fill_color: RGB color for redaction box (0-1 range). Default is black (0,0,0)
        overlay_text: Default text to display over redacted areas (can be overridden per redaction)
    
    Returns:
        JSON string with summary of redactions applied
    """
    try:
        pdf_path = resolve_pdf_path(pdf_path)
        output_path = resolve_pdf_path(output_path)
        doc = pymupdf.open(pdf_path)
        applied_redactions = []
        
        for redaction in redactions:
            page_num = redaction.get("page", 0)
            bbox = redaction.get("bbox")
            redact_text = redaction.get("text", overlay_text)
            
            if page_num < 0 or page_num >= len(doc):
                applied_redactions.append({
                    "status": "error",
                    "message": f"Invalid page number {page_num}"
                })
                continue
            
            if not bbox or len(bbox) != 4:
                applied_redactions.append({
                    "status": "error",
                    "message": "Invalid bbox format. Expected [x0, y0, x1, y1]"
                })
                continue
            
            page = doc[page_num]
            rect = pymupdf.Rect(bbox)
            
            page.add_redact_annot(
                rect,
                text=redact_text,
                fill=fill_color
            )
            
            applied_redactions.append({
                "page": page_num,
                "bbox": bbox,
                "status": "applied"
            })
        
        # Apply all redactions
        for page in doc:
            page.apply_redactions()
        
        doc.save(output_path)
        doc.close()
        
        result = {
            "input_file": pdf_path,
            "output_file": output_path,
            "total_redactions": len([r for r in applied_redactions if r.get("status") == "applied"]),
            "redactions": applied_redactions
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redact_images_in_pdf(
    pdf_path: str,
    output_path: str,
    page_numbers: Optional[List[int]] = None,
    fill_color: Tuple[float, float, float] = (0, 0, 0),
    overlay_text: str = "[IMAGE REDACTED]"
) -> str:
    """Redact all images in specified pages of a PDF.
    
    Args:
        pdf_path: Path to the input PDF file
        output_path: Path where the redacted PDF will be saved
        page_numbers: List of page numbers to process (0-indexed). If None, processes all pages
        fill_color: RGB color for redaction box (0-1 range). Default is black (0,0,0)
        overlay_text: Text to display over redacted images
    
    Returns:
        JSON string with summary of image redactions
    """
    try:
        pdf_path = resolve_pdf_path(pdf_path)
        output_path = resolve_pdf_path(output_path)
        doc = pymupdf.open(pdf_path)
        total_images_redacted = 0
        summary = []
        
        pages_to_process = page_numbers if page_numbers is not None else list(range(len(doc)))
        
        for page_num in pages_to_process:
            if page_num < 0 or page_num >= len(doc):
                continue
                
            page = doc[page_num]
            images = page.get_images()
            page_images = 0
            
            for img_index, img in enumerate(images):
                # Get image bounding box
                bbox = page.get_image_bbox(img[7])  # img[7] is the image name/xref
                
                if bbox.is_infinite:
                    continue
                
                # Add redaction annotation
                page.add_redact_annot(
                    bbox,
                    text=overlay_text,
                    fill=fill_color,
                    text_color=(1, 1, 1)
                )
                page_images += 1
                total_images_redacted += 1
            
            if page_images > 0:
                # Apply redactions with image removal
                page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE)
                summary.append({
                    "page": page_num,
                    "images_redacted": page_images
                })
        
        doc.save(output_path)
        doc.close()
        
        result = {
            "input_file": pdf_path,
            "output_file": output_path,
            "total_images_redacted": total_images_redacted,
            "pages_processed": len(summary),
            "summary": summary
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def verify_redactions(
    original_pdf: str,
    redacted_pdf: str,
    search_strings: Optional[List[str]] = None
) -> str:
    """Verify that redactions were applied correctly by comparing original and redacted PDFs.
    
    Args:
        original_pdf: Path to the original PDF file
        redacted_pdf: Path to the redacted PDF file
        search_strings: Optional list of strings that should no longer appear in redacted PDF
    
    Returns:
        JSON string with verification results
    """
    try:
        original_pdf = resolve_pdf_path(original_pdf)
        redacted_pdf = resolve_pdf_path(redacted_pdf)
        orig_doc = pymupdf.open(original_pdf)
        redact_doc = pymupdf.open(redacted_pdf)
        redact_doc = pymupdf.open(redacted_pdf)
        
        verification = {
            "original_pages": len(orig_doc),
            "redacted_pages": len(redact_doc),
            "pages_match": len(orig_doc) == len(redact_doc),
            "string_checks": [],
            "text_comparison": []
        }
        
        # Check if specified strings still exist
        if search_strings:
            for search_str in search_strings:
                found_in_redacted = False
                pages_found = []
                
                for page_num in range(len(redact_doc)):
                    page = redact_doc[page_num]
                    rects = page.search_for(search_str)
                    if rects:
                        found_in_redacted = True
                        pages_found.append(page_num)
                
                verification["string_checks"].append({
                    "search_string": search_str,
                    "found_in_redacted": found_in_redacted,
                    "pages_found": pages_found,
                    "status": "FAIL" if found_in_redacted else "PASS"
                })
        
        # Compare text content page by page
        for page_num in range(min(len(orig_doc), len(redact_doc))):
            orig_text = orig_doc[page_num].get_text("text")
            redact_text = redact_doc[page_num].get_text("text")
            
            orig_words = len(orig_text.split())
            redact_words = len(redact_text.split())
            
            verification["text_comparison"].append({
                "page": page_num,
                "original_word_count": orig_words,
                "redacted_word_count": redact_words,
                "words_removed": orig_words - redact_words,
                "text_modified": orig_text != redact_text
            })
        
        orig_doc.close()
        redact_doc.close()
        
        # Overall verdict
        all_checks_passed = all(
            check["status"] == "PASS" 
            for check in verification["string_checks"]
        )
        
        verification["overall_verdict"] = {
            "status": "PASS" if all_checks_passed else "FAIL",
            "message": "All redactions verified successfully" if all_checks_passed 
                      else "Some redactions may have failed"
        }
        
        return json.dumps(verification, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_pdf_info(pdf_path: str) -> str:
    """Get basic information about a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        JSON string with PDF metadata and structure information
    """
    try:
        pdf_path = resolve_pdf_path(pdf_path)
        doc = pymupdf.open(pdf_path)
        
        info = {
            "filename": pdf_path,
            "pages": len(doc),
            "metadata": doc.metadata,
            "is_encrypted": doc.is_encrypted,
            "page_info": []
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_info = {
                "page_number": page_num,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "image_count": len(page.get_images()),
                "link_count": len(list(page.get_links())),
            }
            info["page_info"].append(page_info)
        
        doc.close()
        return json.dumps(info, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


def main():
    """Main entry point for the MCP server."""
    mcp.run()


# ============================================================================
# BASE64 TOOLS - For working with uploaded PDFs (mobile/web apps)
# ============================================================================


@mcp.tool()
def extract_text_from_pdf_base64(
    pdf_data: str,
    page_number: Optional[int] = None,
    format: str = "text"
) -> str:
    """Extract text from a base64-encoded PDF file for LLM consumption.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    
    Args:
        pdf_data: Base64-encoded PDF file
        page_number: Specific page number to extract (0-indexed). If None, extracts all pages
        format: Output format - "text" (plain text), "json" (structured), or "blocks" (text blocks)
    
    Returns:
        Extracted text content in the specified format
    """
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_data)
        
        # Open from memory
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        if page_number is not None:
            if page_number < 0 or page_number >= len(doc):
                doc.close()
                return json.dumps({"error": f"Invalid page number. PDF has {len(doc)} pages"})
            pages_to_process = [page_number]
        else:
            pages_to_process = range(len(doc))
        
        if format == "json":
            result = {
                "total_pages": len(doc),
                "pages": []
            }
            
            for page_num in pages_to_process:
                page = doc[page_num]
                result["pages"].append({
                    "page_number": page_num,
                    "text": page.get_text("text"),
                    "word_count": len(page.get_text("text").split())
                })
            
            doc.close()
            return json.dumps(result, indent=2)
        
        elif format == "blocks":
            result = {
                "total_pages": len(doc),
                "pages": []
            }
            
            for page_num in pages_to_process:
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                result["pages"].append({
                    "page_number": page_num,
                    "blocks": blocks
                })
            
            doc.close()
            return json.dumps(result, indent=2)
        
        else:  # plain text
            text_parts = []
            for page_num in pages_to_process:
                page = doc[page_num]
                text_parts.append(f"=== Page {page_num + 1} ===\n{page.get_text('text')}\n")
            
            doc.close()
            return "\n".join(text_parts)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_text_in_pdf_base64(
    pdf_data: str,
    search_string: str,
    case_sensitive: bool = False,
    use_regex: bool = False,
    page_number: Optional[int] = None
) -> str:
    """Search for text in a base64-encoded PDF and return all occurrences with their locations.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    
    Args:
        pdf_data: Base64-encoded PDF file
        search_string: Text or regex pattern to search for
        case_sensitive: Whether search should be case sensitive
        use_regex: Whether to treat search_string as a regex pattern
        page_number: Specific page to search (0-indexed). If None, searches all pages
    
    Returns:
        JSON string containing all matches with page numbers and bounding boxes
    """
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_data)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        matches = []
        pages_to_search = [page_number] if page_number is not None else range(len(doc))
        
        for page_num in pages_to_search:
            page = doc[page_num]
            
            if use_regex:
                # Extract text and search with regex
                text = page.get_text("text")
                flags = 0 if case_sensitive else re.IGNORECASE
                regex_matches = re.finditer(search_string, text, flags)
                
                for match in regex_matches:
                    # Find the bounding box for this text
                    rects = page.search_for(match.group())
                    for rect in rects:
                        matches.append({
                            "page": page_num,
                            "text": match.group(),
                            "bbox": list(rect),
                            "match_type": "regex"
                        })
            else:
                # Use pymupdf's built-in search
                flags = 0
                if not case_sensitive:
                    flags |= pymupdf.TEXT_PRESERVE_WHITESPACE
                
                rects = page.search_for(search_string)
                for rect in rects:
                    matches.append({
                        "page": page_num,
                        "text": search_string,
                        "bbox": list(rect),
                        "match_type": "exact"
                    })
        
        doc.close()
        
        result = {
            "search_string": search_string,
            "total_matches": len(matches),
            "matches": matches
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redact_text_by_search_base64(
    pdf_data: str,
    search_strings: List[str],
    case_sensitive: bool = False,
    fill_color: Tuple[float, float, float] = (0, 0, 0),
    overlay_text: str = "",
    text_color: Tuple[float, float, float] = (1, 1, 1)
) -> str:
    """Redact all occurrences of specified text strings in a base64-encoded PDF.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    Returns a base64-encoded redacted PDF.
    
    Args:
        pdf_data: Base64-encoded PDF file
        search_strings: List of strings to search for and redact
        case_sensitive: Whether search should be case sensitive
        fill_color: RGB color for redaction box (0-1 range). Default is black (0,0,0)
        overlay_text: Optional text to display over redacted area
        text_color: RGB color for overlay text (0-1 range). Default is white (1,1,1)
    
    Returns:
        JSON string with base64-encoded redacted PDF and summary of redactions
    """
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_data)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        total_redactions = 0
        redaction_summary = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_redactions = 0
            
            for search_string in search_strings:
                # Search for all occurrences
                rects = page.search_for(search_string)
                
                for rect in rects:
                    # Add redaction annotation
                    page.add_redact_annot(
                        rect,
                        text=overlay_text,
                        fill=fill_color,
                        text_color=text_color
                    )
                    page_redactions += 1
                    total_redactions += 1
            
            if page_redactions > 0:
                # Apply all redactions on this page
                page.apply_redactions()
                redaction_summary.append({
                    "page": page_num,
                    "redactions": page_redactions
                })
        
        # Save to BytesIO
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()
        
        # Encode to base64
        output_buffer.seek(0)
        redacted_pdf_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        result = {
            "redacted_pdf": redacted_pdf_base64,
            "total_redactions": total_redactions,
            "pages_modified": len(redaction_summary),
            "summary": redaction_summary,
            "search_strings": search_strings
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redact_by_coordinates_base64(
    pdf_data: str,
    redactions: List[Dict[str, Any]],
    fill_color: Tuple[float, float, float] = (0, 0, 0),
    overlay_text: str = ""
) -> str:
    """Redact specific areas of a base64-encoded PDF by coordinates.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    Returns a base64-encoded redacted PDF.
    
    Args:
        pdf_data: Base64-encoded PDF file
        redactions: List of redaction areas, each with:
            - page: Page number (0-indexed)
            - bbox: Bounding box as [x0, y0, x1, y1]
            - text: Optional overlay text for this specific redaction
        fill_color: RGB color for redaction box (0-1 range). Default is black (0,0,0)
        overlay_text: Default text to display over redacted areas (can be overridden per redaction)
    
    Returns:
        JSON string with base64-encoded redacted PDF and summary of redactions
    """
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_data)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        applied_redactions = []
        
        for redaction in redactions:
            page_num = redaction.get("page", 0)
            bbox = redaction.get("bbox")
            redact_text = redaction.get("text", overlay_text)
            
            if page_num < 0 or page_num >= len(doc):
                applied_redactions.append({
                    "status": "error",
                    "message": f"Invalid page number {page_num}"
                })
                continue
            
            if not bbox or len(bbox) != 4:
                applied_redactions.append({
                    "status": "error",
                    "message": "Invalid bbox format. Expected [x0, y0, x1, y1]"
                })
                continue
            
            page = doc[page_num]
            rect = pymupdf.Rect(bbox)
            
            page.add_redact_annot(
                rect,
                text=redact_text,
                fill=fill_color
            )
            
            applied_redactions.append({
                "page": page_num,
                "bbox": bbox,
                "status": "applied"
            })
        
        # Apply all redactions
        for page in doc:
            page.apply_redactions()
        
        # Save to BytesIO
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()
        
        # Encode to base64
        output_buffer.seek(0)
        redacted_pdf_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        result = {
            "redacted_pdf": redacted_pdf_base64,
            "total_redactions": len([r for r in applied_redactions if r.get("status") == "applied"]),
            "redactions": applied_redactions
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redact_images_in_pdf_base64(
    pdf_data: str,
    page_numbers: Optional[List[int]] = None,
    fill_color: Tuple[float, float, float] = (0, 0, 0),
    overlay_text: str = "[IMAGE REDACTED]"
) -> str:
    """Redact all images in specified pages of a base64-encoded PDF.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    Returns a base64-encoded redacted PDF.
    
    Args:
        pdf_data: Base64-encoded PDF file
        page_numbers: List of page numbers to process (0-indexed). If None, processes all pages
        fill_color: RGB color for redaction box (0-1 range). Default is black (0,0,0)
        overlay_text: Text to display over redacted images
    
    Returns:
        JSON string with base64-encoded redacted PDF and summary of image redactions
    """
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_data)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        total_images_redacted = 0
        summary = []
        
        pages_to_process = page_numbers if page_numbers is not None else list(range(len(doc)))
        
        for page_num in pages_to_process:
            if page_num < 0 or page_num >= len(doc):
                continue
                
            page = doc[page_num]
            images = page.get_images()
            page_images = 0
            
            for img_index, img in enumerate(images):
                # Get image bounding box
                bbox = page.get_image_bbox(img[7])  # img[7] is the image name/xref
                
                if bbox.is_infinite:
                    continue
                
                # Add redaction annotation
                page.add_redact_annot(
                    bbox,
                    text=overlay_text,
                    fill=fill_color,
                    text_color=(1, 1, 1)
                )
                page_images += 1
                total_images_redacted += 1
            
            if page_images > 0:
                # Apply redactions with image removal
                page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE)
                summary.append({
                    "page": page_num,
                    "images_redacted": page_images
                })
        
        # Save to BytesIO
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()
        
        # Encode to base64
        output_buffer.seek(0)
        redacted_pdf_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        result = {
            "redacted_pdf": redacted_pdf_base64,
            "total_images_redacted": total_images_redacted,
            "pages_processed": len(summary),
            "summary": summary
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def verify_redactions_base64(
    original_pdf_data: str,
    redacted_pdf_data: str,
    search_strings: Optional[List[str]] = None
) -> str:
    """Verify that redactions were applied correctly by comparing original and redacted base64-encoded PDFs.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    
    Args:
        original_pdf_data: Base64-encoded original PDF file
        redacted_pdf_data: Base64-encoded redacted PDF file
        search_strings: Optional list of strings that should no longer appear in redacted PDF
    
    Returns:
        JSON string with verification results
    """
    try:
        # Decode base64 to bytes
        orig_bytes = base64.b64decode(original_pdf_data)
        redact_bytes = base64.b64decode(redacted_pdf_data)
        
        orig_doc = pymupdf.open(stream=orig_bytes, filetype="pdf")
        redact_doc = pymupdf.open(stream=redact_bytes, filetype="pdf")
        
        verification = {
            "original_pages": len(orig_doc),
            "redacted_pages": len(redact_doc),
            "pages_match": len(orig_doc) == len(redact_doc),
            "string_checks": [],
            "text_comparison": []
        }
        
        # Check if specified strings still exist
        if search_strings:
            for search_str in search_strings:
                found_in_redacted = False
                pages_found = []
                
                for page_num in range(len(redact_doc)):
                    page = redact_doc[page_num]
                    rects = page.search_for(search_str)
                    if rects:
                        found_in_redacted = True
                        pages_found.append(page_num)
                
                verification["string_checks"].append({
                    "search_string": search_str,
                    "found_in_redacted": found_in_redacted,
                    "pages_found": pages_found,
                    "status": "FAIL" if found_in_redacted else "PASS"
                })
        
        # Compare text content page by page
        for page_num in range(min(len(orig_doc), len(redact_doc))):
            orig_text = orig_doc[page_num].get_text("text")
            redact_text = redact_doc[page_num].get_text("text")
            
            orig_words = len(orig_text.split())
            redact_words = len(redact_text.split())
            
            verification["text_comparison"].append({
                "page": page_num,
                "original_word_count": orig_words,
                "redacted_word_count": redact_words,
                "words_removed": orig_words - redact_words,
                "text_modified": orig_text != redact_text
            })
        
        orig_doc.close()
        redact_doc.close()
        
        # Overall verdict
        all_checks_passed = all(
            check["status"] == "PASS" 
            for check in verification["string_checks"]
        )
        
        verification["overall_verdict"] = {
            "status": "PASS" if all_checks_passed else "FAIL",
            "message": "All redactions verified successfully" if all_checks_passed 
                      else "Some redactions may have failed"
        }
        
        return json.dumps(verification, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_pdf_info_base64(pdf_data: str) -> str:
    """Get basic information about a base64-encoded PDF file.
    
    Use this tool when working with uploaded PDFs in mobile/web apps.
    
    Args:
        pdf_data: Base64-encoded PDF file
    
    Returns:
        JSON string with PDF metadata and structure information
    """
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_data)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        info = {
            "pages": len(doc),
            "metadata": doc.metadata,
            "is_encrypted": doc.is_encrypted,
            "page_info": []
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_info = {
                "page_number": page_num,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "image_count": len(page.get_images()),
                "link_count": len(list(page.get_links())),
            }
            info["page_info"].append(page_info)
        
        doc.close()
        return json.dumps(info, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="PDF Redaction MCP Server - Provides PDF redaction tools via Model Context Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Transport Modes:
  stdio       Standard I/O (default) - for Claude Desktop, Cursor, etc.
  http        HTTP transport - for web-based clients
  sse         Server-Sent Events - for mobile apps and remote clients

Examples:
  %(prog)s                                    # Run in STDIO mode (default)
  %(prog)s --transport sse --port 8000        # Run as SSE server on port 8000
  %(prog)s --transport http --host 0.0.0.0    # Run as HTTP server on all interfaces
  %(prog)s --pdf-dir /path/to/pdfs            # Set base directory for PDF files
        """
    )
    
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport mode for the MCP server (default: stdio)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to for HTTP/SSE mode (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on for HTTP/SSE mode (default: 8000)"
    )
    
    parser.add_argument(
        "--pdf-dir",
        type=str,
        default=None,
        help="Base directory for PDF files. Relative paths in tools will be resolved against this directory."
    )
    
    args = parser.parse_args()
    
    # Set global PDF base directory if provided
    global PDF_BASE_DIR
    if args.pdf_dir:
        PDF_BASE_DIR = Path(args.pdf_dir).resolve()
        if not PDF_BASE_DIR.exists():
            print(f"Warning: PDF base directory does not exist: {PDF_BASE_DIR}")
        else:
            print(f"PDF base directory: {PDF_BASE_DIR}")
    
    # Run server with appropriate transport
    if args.transport == "stdio":
        print("Starting PDF Redaction MCP Server in STDIO mode...")
        mcp.run()
    elif args.transport in ("http", "sse"):
        print(f"Starting PDF Redaction MCP Server in {args.transport.upper()} mode...")
        print(f"Listening on {args.host}:{args.port}")
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Allow all origins; use specific origins for security
                allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
                allow_headers=[
                    "mcp-protocol-version",
                    "mcp-session-id",
                    "Authorization",
                    "Content-Type",
                ],
                expose_headers=["mcp-session-id"],            )
        ]
        app = mcp.http_app(middleware=middleware)
        
        uvicorn.run(app, host=args.host, port=args.port)
        #mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
