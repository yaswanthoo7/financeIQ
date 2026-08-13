"""
Pytest unit & integration tests for FinanceIQ API endpoints.
"""
import pytest
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "FinanceIQ"


def test_upload_invalid_file_type():
    file_content = b"fake pdf content"
    files = {"files": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["failed"] == 1
    assert "Unsupported file type" in data["uploads"][0]["message"]


def test_upload_empty_file():
    files = {"files": ("test.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["failed"] == 1
    assert "empty" in data["uploads"][0]["message"].lower()


def test_upload_corrupted_pdf():
    files = {"files": ("test.pdf", io.BytesIO(b"NOT A REAL PDF HEADER"), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["failed"] == 1
    assert "corrupted" in data["uploads"][0]["message"].lower()


def test_records_list_requires_session():
    """Listing records without a session should fail."""
    response = client.get("/api/records")
    assert response.status_code == 400


def test_categories_list_requires_session():
    """Listing categories without a session should fail."""
    response = client.get("/api/categories")
    assert response.status_code == 400
