"""
GATE-04 Tests: Verification & Anomaly API Endpoints

Verifies:
- POST /api/documents/{id}/verify
- GET /api/farmers/{id}/anomalies
- GET /api/farmers/{id}/review-queue
- POST /api/anomalies/{id}/resolve
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.repositories import (
    get_anomaly_repo, get_document_repo, get_document_field_repo,
    get_standardized_record_repo, get_verification_repo,
)


FAKE_PDF = b"%PDF-1.4 gate04 api test content"


class TestVerifyEndpoint:
    """Test POST /api/documents/{id}/verify."""

    def _upload_and_normalize(self, client):
        """Upload, confirm, normalize a document. Return doc_id."""
        get_document_repo().clear()
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()
        get_verification_repo().clear()
        get_anomaly_repo().clear()

        resp = client.post(
            "/api/documents/upload",
            files={"file": ("verify_test.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-api-ver", "domain": "CERTIFICATION"},
        )
        doc_id = resp.json()["document"]["id"]
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        client.post(f"/api/documents/{doc_id}/normalize")
        return doc_id

    def test_verify_returns_200(self, client, test_data_dir):
        doc_id = self._upload_and_normalize(client)
        response = client.post(f"/api/documents/{doc_id}/verify")
        assert response.status_code == 200

    def test_verify_returns_verifications(self, client, test_data_dir):
        doc_id = self._upload_and_normalize(client)
        response = client.post(f"/api/documents/{doc_id}/verify")
        data = response.json()
        assert "verifications" in data
        assert len(data["verifications"]) > 0

    def test_verify_returns_anomalies_list(self, client, test_data_dir):
        doc_id = self._upload_and_normalize(client)
        response = client.post(f"/api/documents/{doc_id}/verify")
        data = response.json()
        assert "anomalies" in data
        assert "anomaly_count" in data

    def test_verify_updates_status(self, client, test_data_dir):
        doc_id = self._upload_and_normalize(client)
        client.post(f"/api/documents/{doc_id}/verify")
        response = client.get(f"/api/documents/{doc_id}")
        assert response.json()["status"] == "VERIFIED"

    def test_verify_no_records_returns_400(self, client, test_data_dir):
        get_document_repo().clear()
        get_document_field_repo().clear()
        # Upload but don't normalize
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("no_norm.pdf", b"%PDF no normalize", "application/pdf")},
            data={"farmer_id": "farmer-no-norm", "domain": "IDENTITY"},
        )
        doc_id = resp.json()["document"]["id"]
        response = client.post(f"/api/documents/{doc_id}/verify")
        assert response.status_code == 400

    def test_verify_nonexistent_returns_404(self, client, test_data_dir):
        response = client.post("/api/documents/no-such-doc/verify")
        assert response.status_code == 404


class TestAnomaliesEndpoint:
    """Test GET /api/farmers/{id}/anomalies."""

    def test_get_farmer_anomalies(self, client, test_data_dir):
        get_document_repo().clear()
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()
        get_verification_repo().clear()
        get_anomaly_repo().clear()

        # Upload, normalize, verify
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("anom_test.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-anom-api", "domain": "CERTIFICATION"},
        )
        doc_id = resp.json()["document"]["id"]
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        client.post(f"/api/documents/{doc_id}/normalize")
        client.post(f"/api/documents/{doc_id}/verify")

        response = client.get("/api/farmers/farmer-anom-api/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "unresolved" in data
        assert "anomalies" in data


class TestReviewQueueEndpoint:
    """Test GET /api/farmers/{id}/review-queue."""

    def test_review_queue_endpoint(self, client, test_data_dir):
        response = client.get("/api/farmers/farmer-anom-api/review-queue")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "items" in data


class TestResolveEndpoint:
    """Test POST /api/anomalies/{id}/resolve."""

    def test_resolve_anomaly(self, client, test_data_dir):
        get_anomaly_repo().clear()
        get_standardized_record_repo().clear()

        from backend.app.models import Anomaly, AnomalyType, AnomalySeverity, StandardizedRecord, DataDomain, SourceLevel
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="resolve-rec", document_id="resolve-doc", farmer_id="farmer-resolve",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V1, data={},
        ))
        anomaly_repo = get_anomaly_repo()
        anomaly_repo.create(Anomaly(
            id="resolve-anom", record_id="resolve-rec",
            anomaly_type=AnomalyType.EXPIRED, severity=AnomalySeverity.CRITICAL,
            description="test", is_resolved=False,
        ))

        response = client.post(
            "/api/anomalies/resolve-anom/resolve",
            json={"resolved_by": "reviewer", "notes": "Checked manually"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

        # Verify persisted
        loaded = anomaly_repo.get_by_id("resolve-anom")
        assert loaded.is_resolved is True

    def test_resolve_nonexistent_returns_404(self, client, test_data_dir):
        response = client.post(
            "/api/anomalies/no-such-anomaly/resolve",
            json={"resolved_by": "x"},
        )
        assert response.status_code == 404

    def test_resolve_already_resolved_returns_400(self, client, test_data_dir):
        get_anomaly_repo().clear()
        get_standardized_record_repo().clear()

        from backend.app.models import Anomaly, AnomalyType, AnomalySeverity
        anomaly_repo = get_anomaly_repo()
        anomaly_repo.create(Anomaly(
            id="already-resolved", record_id="x",
            anomaly_type=AnomalyType.DUPLICATE, severity=AnomalySeverity.WARNING,
            description="done", is_resolved=True, resolved_by="prev",
        ))

        response = client.post(
            "/api/anomalies/already-resolved/resolve",
            json={"resolved_by": "x"},
        )
        assert response.status_code == 400
