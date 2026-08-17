# GreenFin Domain Model

## Core Entities

| Entity | Purpose |
|---|---|
| User | 系統帳號 |
| FarmerProfile | 小農身分與設定 |
| BankInstitution | 金融機構 |
| Farm | 農場 |
| Crop | 作物 |
| Document | 原始文件 |
| DocumentField | OCR / 人工確認欄位 |
| StandardizedRecord | 標準化後資料 |
| VerificationResult | V0–V3 與核驗理由 |
| Anomaly | 異常 |
| GreenAction | 綠色行動 |
| ExperienceTransaction | 經驗值逐筆計算 |
| IndicatorResult | 四大指標結果 |
| DataHealthResult | 分項 Data Health |
| RuleSet | 規則版本 |
| Authorization | 小農授權 |
| BankCase | 銀行端案件視圖 |
| AuditLog | 稽核軌跡 |

## Conceptual Relationships

```mermaid
erDiagram
    USER ||--o| FARMER_PROFILE : has
    FARMER_PROFILE ||--o{ FARM : owns
    FARM ||--o{ CROP : grows
    FARMER_PROFILE ||--o{ DOCUMENT : uploads
    DOCUMENT ||--o{ DOCUMENT_FIELD : extracts
    DOCUMENT ||--o{ STANDARDIZED_RECORD : produces
    STANDARDIZED_RECORD ||--o{ VERIFICATION_RESULT : verified_by
    STANDARDIZED_RECORD ||--o{ ANOMALY : may_have
    STANDARDIZED_RECORD ||--o{ GREEN_ACTION : supports
    GREEN_ACTION ||--o{ EXPERIENCE_TRANSACTION : produces
    RULE_SET ||--o{ EXPERIENCE_TRANSACTION : calculates
    RULE_SET ||--o{ INDICATOR_RESULT : calculates
    RULE_SET ||--o{ DATA_HEALTH_RESULT : calculates
    FARMER_PROFILE ||--o{ AUTHORIZATION : grants
    BANK_INSTITUTION ||--o{ AUTHORIZATION : receives
    AUTHORIZATION ||--o{ BANK_CASE : enables
```

## Design Rule

所有計算結果應保留足夠 Foreign Key / Reference 以支援：

```text
Result → Rule → Structured Record → Evidence → Original Document
```
