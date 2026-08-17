"""
GATE-03 Tests: Document Pipeline API Endpoints

Verifies:
- POST /api/documents/upload (valid, invalid type, duplicate)
- GET /api/documents/{id}
- GET /api/documents/{id}/fields
- POST /api/documents/{id}/confirm
- POST /api/documents/{id}/normalize
- GET /api/farmers/{id}/documents
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.repositories import get_document_repo, get_document_field_repo, get_standardized_record_repo


FAKE_PDF = b"%PDF-1.4 test content for API"


class TestUploadEndpoint:
    """Test POST /api/documents/upload."""

    def test_upload_valid_pdf(self, client, test_data_dir):
        get_document_repo().clear()
        get_document_field_repo().clear()

        response = client.post(
            "/api/documents/upload",
            files={"file": ("cert.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-api-1", "domain": "CERTIFICATION"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert "fields" in data
        assert data["document"]["filename"] == "cert.pdf"
        assert data["document"]["status"] == "OCR_COMPLETED"
        assert len(data["fields"]) > 0

    def test_upload_invalid_type(self, client, test_data_dir):
        response = client.post(
            "/api/documents/upload",
            files={"file": ("bad.exe", b"malware", "application/x-executable")},
            data={"farmer_id": "farmer-api-2", "domain": "IDENTITY"},
        )
        assert response.status_code == 400
        assert "INVALID_FILE_TYPE" in str(response.json())

    def test_upload_invalid_domain(self, client, test_data_dir):
        response = client.post(
            "/api/documents/upload",
            files={"file": ("doc.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-api-3", "domain": "INVALID_DOMAIN"},
        )
        assert response.status_code == 400

    def test_upload_duplicate_rejected(self, client, test_data_dir):
        get_document_repo().clear()
        get_document_field_repo().clear()

        # First upload
        client.post(
            "/api/documents/upload",
            files={"file": ("first.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-api-dup", "domain": "TRANSACTION"},
        )
        # Second upload same content
        response = client.post(
            "/api/documents/upload",
            files={"file": ("second.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-api-dup", "domain": "TRANSACTION"},
        )
        assert response.status_code == 400
        assert "DUPLICATE_FILE" in str(response.json())


class TestDocumentEndpoints:
    """Test GET/POST document detail endpoints."""

    def _upload_and_get_id(self, client):
        """Helper: upload a document and return its ID."""
        get_document_repo().clear()
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()

        resp = client.post(
            "/api/documents/upload",
            files={"file": ("api_test.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-api-detail", "domain": "CERTIFICATION"},
        )
        return resp.json()["document"]["id"]

    def test_get_document(self, client, test_data_dir):
        doc_id = self._upload_and_get_id(client)
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["id"] == doc_id

    def test_get_document_not_found(self, client, test_data_dir):
        response = client.get("/api/documents/nonexistent-id")
        assert response.status_code == 404

    def test_get_document_fields(self, client, test_data_dir):
        doc_id = self._upload_and_get_id(client)
        response = client.get(f"/api/documents/{doc_id}/fields")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert len(data["fields"]) > 0

    def test_confirm_fields(self, client, test_data_dir):
        doc_id = self._upload_and_get_id(client)
        response = client.post(
            f"/api/documents/{doc_id}/confirm",
            json={"corrections": {}},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "FIELDS_CONFIRMED"

    def test_normalize_document(self, client, test_data_dir):
        doc_id = self._upload_and_get_id(client)
        # First confirm
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        # Then normalize
        response = client.post(f"/api/documents/{doc_id}/normalize")
        assert response.status_code == 200
        data = response.json()
        assert "record" in data
        assert data["record"]["document_id"] == doc_id
        assert data["record"]["domain"] == "CERTIFICATION"

    def test_get_document_record(self, client, test_data_dir):
        doc_id = self._upload_and_get_id(client)
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        client.post(f"/api/documents/{doc_id}/normalize")

        response = client.get(f"/api/documents/{doc_id}/record")
        assert response.status_code == 200
        assert response.json()["record_type"] == "certification_record"


class TestFarmerDocumentsEndpoint:
    """Test GET /api/farmers/{id}/documents."""

    def test_farmer_documents_list(self, client, test_data_dir):
        get_document_repo().clear()
        get_document_field_repo().clear()

        # Upload two documents for same farmer
        client.post(
            "/api/documents/upload",
            files={"file": ("doc1.pdf", b"%PDF doc1 content", "application/pdf")},
            data={"farmer_id": "farmer-list", "domain": "CERTIFICATION"},
        )
        client.post(
            "/api/documents/upload",
            files={"file": ("doc2.pdf", b"%PDF doc2 content", "application/pdf")},
            data={"farmer_id": "farmer-list", "domain": "TRANSACTION"},
        )

        response = client.get("/api/farmers/farmer-list/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["farmer_id"] == "farmer-list"
        assert data["count"] == 2

    def test_farmer_documents_empty(self, client, test_data_dir):
        get_document_repo().clear()
        response = client.get("/api/farmers/no-docs-farmer/documents")
        assert response.status_code == 200
        assert response.json()["count"] == 0
