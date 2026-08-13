"""
Pytest unit tests for edge cases (file validation, prompt formatting, enums).
"""
import pytest
from app.utils.file_validation import get_file_extension, detect_file_type
from app.utils.prompts import FINANCIAL_RECORD_EXTRACTION_PROMPT, NL_QUERY_PROMPT
from app.models.enums import RecordType, RecordStatus, CategoryGroup, POStatus


def test_file_extension_parsing():
    assert get_file_extension("invoice.pdf") == ".pdf"
    assert get_file_extension("RECEIPT.PNG") == ".png"
    assert get_file_extension("document.tar.gz") == ".gz"
    assert get_file_extension("noextension") == ""


def test_magic_bytes_detection():
    assert detect_file_type(b"%PDF-1.5") == ".pdf"
    assert detect_file_type(b"\x89PNG\r\n\x1a\n") == ".png"
    assert detect_file_type(b"\xff\xd8\xff\xe0") == ".jpg"
    assert detect_file_type(b"UNKNOWN") is None


def test_nl_query_prompt_formatting():
    formatted_prompt = NL_QUERY_PROMPT.format(today="2026-08-13", query="receipts over 500")
    assert "2026-08-13" in formatted_prompt
    assert "receipts over 500" in formatted_prompt
    assert "record_type" in formatted_prompt
    assert "category_name" in formatted_prompt


def test_extraction_prompt_has_all_types():
    """The extraction prompt should mention all four document types."""
    prompt = FINANCIAL_RECORD_EXTRACTION_PROMPT
    assert "invoice" in prompt.lower()
    assert "receipt" in prompt.lower()
    assert "purchase_order" in prompt.lower()
    assert "expense_report" in prompt.lower()


def test_record_type_enum():
    assert RecordType.INVOICE.value == "invoice"
    assert RecordType.RECEIPT.value == "receipt"
    assert RecordType.PURCHASE_ORDER.value == "purchase_order"
    assert RecordType.EXPENSE_REPORT.value == "expense_report"


def test_record_status_enum():
    assert RecordStatus.PROCESSING.value == "processing"
    assert RecordStatus.COMPLETED.value == "completed"
    assert RecordStatus.NEEDS_REVIEW.value == "needs_review"
    assert RecordStatus.FAILED.value == "failed"


def test_category_group_enum():
    assert CategoryGroup.BUSINESS.value == "business"
    assert CategoryGroup.PERSONAL.value == "personal"
    assert CategoryGroup.CUSTOM.value == "custom"


def test_po_status_enum():
    assert POStatus.DRAFT.value == "draft"
    assert POStatus.SUBMITTED.value == "submitted"
    assert POStatus.APPROVED.value == "approved"
    assert POStatus.FULFILLED.value == "fulfilled"
