"""
GATE-03 Tests: Mock OCR Provider

Verifies:
- MockOCRProvider implements OCRProvider interface
- Returns domain-specific fields
- All domains produce results
- Confidence values are in valid range
- Provider name is set correctly
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models.enums import DataDomain
from backend.app.services.ocr.provider import (
    MockOCRProvider,
    OCRProvider,
    OCRResult,
    get_ocr_provider,
)


FAKE_CONTENT = b"fake file content for OCR"


class TestOCRProviderInterface:
    """Test OCR provider interface compliance."""

    def test_mock_provider_is_ocr_provider(self):
        provider = MockOCRProvider()
        assert isinstance(provider, OCRProvider)

    def test_get_ocr_provider_returns_mock(self):
        provider = get_ocr_provider()
        assert isinstance(provider, MockOCRProvider)


class TestMockOCRExtraction:
    """Test Mock OCR extraction results."""

    def test_certification_domain_fields(self):
        provider = MockOCRProvider()
        result = provider.extract(FAKE_CONTENT, "cert.pdf", "application/pdf", DataDomain.CERTIFICATION)
        assert result.success is True
        assert len(result.fields) >= 3
        field_names = [f.field_name for f in result.fields]
        assert "認證機構" in field_names
        assert "有效期限" in field_names

    def test_transaction_domain_fields(self):
        provider = MockOCRProvider()
        result = provider.extract(FAKE_CONTENT, "invoice.pdf", "application/pdf", DataDomain.TRANSACTION)
        assert result.success is True
        field_names = [f.field_name for f in result.fields]
        assert "交易金額" in field_names
        assert "交易日期" in field_names

    def test_green_action_domain_fields(self):
        provider = MockOCRProvider()
        result = provider.extract(FAKE_CONTENT, "photo.jpg", "image/jpeg", DataDomain.GREEN_ACTION)
        assert result.success is True
        field_names = [f.field_name for f in result.fields]
        assert "活動名稱" in field_names

    def test_all_domains_produce_results(self):
        provider = MockOCRProvider()
        for domain in DataDomain:
            result = provider.extract(FAKE_CONTENT, "test.pdf", "application/pdf", domain)
            assert result.success is True
            assert len(result.fields) > 0

    def test_confidence_values_valid_range(self):
        provider = MockOCRProvider()
        for domain in DataDomain:
            result = provider.extract(FAKE_CONTENT, "test.pdf", "application/pdf", domain)
            for field in result.fields:
                assert 0.0 <= field.confidence <= 1.0, f"Invalid confidence for {field.field_name}"

    def test_result_provider_name(self):
        provider = MockOCRProvider()
        result = provider.extract(FAKE_CONTENT, "test.pdf", "application/pdf", DataDomain.IDENTITY)
        assert result.provider == "MockOCRProvider"

    def test_result_has_raw_text(self):
        provider = MockOCRProvider()
        result = provider.extract(FAKE_CONTENT, "cert.pdf", "application/pdf", DataDomain.CERTIFICATION)
        assert "DEMO SIMULATED OCR" in result.raw_text
