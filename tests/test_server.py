"""Tests for PDF Redaction MCP Server."""

import pytest
import json
from pathlib import Path


def test_server_import():
    """Test that the server module can be imported."""
    from pdf_redaction_mcp.server import mcp
    assert mcp is not None
    assert mcp.name == "PDF Redaction Server"


def test_tools_registered():
    """Test that all expected tools are registered."""
    from pdf_redaction_mcp.server import mcp
    
    expected_tools = [
        "load_pdf",
        "save_pdf",
        "close_pdf",
        "list_loaded_pdfs",
        "extract_text_from_pdf",
        "search_text_in_pdf",
        "redact_text_by_search",
        "redact_by_coordinates",
        "redact_images_in_pdf",
        "verify_redactions",
        "get_pdf_info"
    ]
    
    # Get all tool definitions from the MCP server
    tool_names = []
    for item in dir(mcp):
        attr = getattr(mcp, item)
        # Check if it's a tool (has a 'name' attribute and is a tool)
        if hasattr(attr, 'name') and hasattr(attr, '__call__'):
            # This is a decorated tool
            continue
    
    # Alternative: check that the functions exist in the server module
    from pdf_redaction_mcp import server
    for expected_tool in expected_tools:
        assert hasattr(server, expected_tool), f"Function {expected_tool} not found in server module"


def test_extract_text_error_handling():
    """Test error handling for non-existent document ID."""
    # Import the actual function, not the decorated version
    from pdf_redaction_mcp import server
    
    # Get the actual function before decoration
    extract_fn = server.extract_text_from_pdf
    if hasattr(extract_fn, 'fn'):
        extract_fn = extract_fn.fn
    
    result = extract_fn(
        document_id="nonexistent_doc",
        format="text"
    )
    
    # Should return error as JSON
    result_dict = json.loads(result)
    assert "error" in result_dict
    assert "not found" in result_dict["error"].lower()


def test_search_text_error_handling():
    """Test error handling for search in non-existent document."""
    from pdf_redaction_mcp import server
    
    # Get the actual function
    search_fn = server.search_text_in_pdf
    if hasattr(search_fn, 'fn'):
        search_fn = search_fn.fn
    
    result = search_fn(
        document_id="nonexistent_doc",
        search_string="test"
    )
    
    # Should return error as JSON
    result_dict = json.loads(result)
    assert "error" in result_dict
    assert "not found" in result_dict["error"].lower()


def test_get_pdf_info_error_handling():
    """Test error handling for PDF info on non-existent document."""
    from pdf_redaction_mcp import server
    
    # Get the actual function
    info_fn = server.get_pdf_info
    if hasattr(info_fn, 'fn'):
        info_fn = info_fn.fn
    
    result = info_fn(document_id="nonexistent_doc")
    
    # Should return error as JSON
    result_dict = json.loads(result)
    assert "error" in result_dict
    assert "not found" in result_dict["error"].lower()


def test_load_pdf_error_handling():
    """Test error handling for loading non-existent PDF file."""
    from pdf_redaction_mcp import server
    
    # Get the actual function
    load_fn = server.load_pdf
    if hasattr(load_fn, 'fn'):
        load_fn = load_fn.fn
    
    result = load_fn(pdf_path="/nonexistent/file.pdf")
    
    # Should return error as JSON
    result_dict = json.loads(result)
    assert "error" in result_dict


def test_list_loaded_pdfs():
    """Test listing loaded PDFs when none are loaded."""
    from pdf_redaction_mcp import server
    
    # Clear any loaded documents first
    server.DOCUMENT_STORE.clear()
    
    # Get the actual function
    list_fn = server.list_loaded_pdfs
    if hasattr(list_fn, 'fn'):
        list_fn = list_fn.fn
    
    result = list_fn()
    
    # Should return valid JSON with empty list
    result_dict = json.loads(result)
    assert "total_documents" in result_dict
    assert result_dict["total_documents"] == 0
    assert "documents" in result_dict
    assert len(result_dict["documents"]) == 0


# Note: Full integration tests would require actual PDF files
# These would be added in a real-world scenario with test fixtures
