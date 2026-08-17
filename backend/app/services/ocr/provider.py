"""
OCR Provider Interface and Mock Implementation.

Per AGENTS.md §14:
- Must use Provider/Adapter interface
- Demo implements MockOCRProvider
- Interface ready for: PaddleOCR, Google Vision, Azure Document Intelligence, LLM Vision

OCR Data Flow:
  Raw OCR → Extracted Fields → Human Confirmation → Normalized Fields
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from backend.app.models.enums import DataDomain


@dataclass
class OCRField:
    """A single field extracted by OCR."""
    field_name: str
    raw_value: str
    confidence: float  # 0.0 - 1.0
    bounding_box: Optional[dict] = None  # For future use


@dataclass
class OCRResult:
    """Result of OCR processing on a document."""
    success: bool
    fields: list[OCRField] = field(default_factory=list)
    raw_text: str = ""
    provider: str = "unknown"
    error: Optional[str] = None


class OCRProvider(ABC):
    """Abstract base class for OCR providers."""

    @abstractmethod
    def extract(self, content: bytes, filename: str, mime_type: str, domain: DataDomain) -> OCRResult:
        """
        Extract text and fields from a document.

        Args:
            content: File bytes.
            filename: Original filename (hints for extraction).
            mime_type: File MIME type.
            domain: Data domain to guide field extraction.

        Returns:
            OCRResult with extracted fields.
        """
        ...


class MockOCRProvider(OCRProvider):
    """
    Mock OCR provider for demo purposes.

    Returns predefined fields based on document domain.
    Simulates realistic OCR with varying confidence levels.
    All results are clearly DEMO / SIMULATED.
    """

    MOCK_FIELDS: dict[str, list[OCRField]] = {
        DataDomain.CERTIFICATION.value: [
            OCRField(field_name="認證機構", raw_value="慈心有機農業發展基金會 (DEMO)", confidence=0.95),
            OCRField(field_name="認證類型", raw_value="有機農產品認證", confidence=0.92),
            OCRField(field_name="有效期限", raw_value="2027/06/30", confidence=0.88),
            OCRField(field_name="認證範圍", raw_value="稻米、蔬菜", confidence=0.85),
            OCRField(field_name="證書編號", raw_value="ORG-2026-00123", confidence=0.97),
        ],
        DataDomain.TRANSACTION.value: [
            OCRField(field_name="交易對象", raw_value="後壁區農會 (DEMO)", confidence=0.93),
            OCRField(field_name="交易金額", raw_value="NT$85,000", confidence=0.90),
            OCRField(field_name="交易日期", raw_value="2026/03/15", confidence=0.87),
            OCRField(field_name="品項", raw_value="有機稻米 500公斤", confidence=0.82),
            OCRField(field_name="單據編號", raw_value="INV-2026-0315", confidence=0.96),
        ],
        DataDomain.GREEN_ACTION.value: [
            OCRField(field_name="活動名稱", raw_value="有機堆肥施用紀錄 (DEMO)", confidence=0.88),
            OCRField(field_name="執行日期", raw_value="2026/04/01", confidence=0.85),
            OCRField(field_name="施用面積", raw_value="0.8 公頃", confidence=0.75),
            OCRField(field_name="堆肥來源", raw_value="自製廚餘堆肥", confidence=0.70),
        ],
        DataDomain.IDENTITY.value: [
            OCRField(field_name="姓名", raw_value="陳○○ (DEMO)", confidence=0.98),
            OCRField(field_name="身分證字號", raw_value="A1234***89", confidence=0.95),
            OCRField(field_name="戶籍地址", raw_value="台南市後壁區○○里", confidence=0.80),
        ],
        DataDomain.LAND_CROP.value: [
            OCRField(field_name="地段", raw_value="後壁段1234地號 (DEMO)", confidence=0.90),
            OCRField(field_name="面積", raw_value="2.5 公頃", confidence=0.88),
            OCRField(field_name="使用分區", raw_value="特定農業區", confidence=0.85),
            OCRField(field_name="登記日期", raw_value="2020/05/12", confidence=0.92),
        ],
        DataDomain.INPUT_EQUIPMENT.value: [
            OCRField(field_name="設備名稱", raw_value="太陽能抽水機 (DEMO)", confidence=0.92),
            OCRField(field_name="購入日期", raw_value="2025/08/01", confidence=0.88),
            OCRField(field_name="金額", raw_value="NT$120,000", confidence=0.90),
            OCRField(field_name="供應商", raw_value="綠能設備有限公司", confidence=0.85),
        ],
        DataDomain.LOAN_PURPOSE.value: [
            OCRField(field_name="申貸用途", raw_value="購置農業設備 (DEMO)", confidence=0.95),
            OCRField(field_name="預估金額", raw_value="NT$500,000", confidence=0.90),
            OCRField(field_name="還款來源", raw_value="農產品銷售收入", confidence=0.85),
        ],
    }

    def extract(self, content: bytes, filename: str, mime_type: str, domain: DataDomain) -> OCRResult:
        """
        Mock extraction — returns predefined fields based on domain.

        Confidence values vary to simulate real OCR behavior.
        """
        fields = self.MOCK_FIELDS.get(domain.value, [
            OCRField(field_name="文件內容", raw_value="(DEMO Mock OCR 無法辨識此類文件)", confidence=0.3),
        ])

        return OCRResult(
            success=True,
            fields=fields,
            raw_text=f"[DEMO SIMULATED OCR] Domain: {domain.value}, File: {filename}",
            provider="MockOCRProvider",
        )


# Default provider for demo
def get_ocr_provider() -> OCRProvider:
    """Get the current OCR provider (Mock for demo)."""
    return MockOCRProvider()
