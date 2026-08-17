# GreenFin Incremental Development Plan

> 強制原則：Build → Test → Verify → Record → Continue

不得 Build Everything → Test at the End。

---

## GATE-01 — Project Foundation

Implementation:
- Repository Structure
- Backend Boot
- Frontend Boot
- Configuration
- Database Connection
- Migration Framework

Tests:
- Backend startup
- Frontend build
- Database connection
- Migration

---

## GATE-02 — Core Data Model

Implementation:
- User
- Farmer
- Farm
- Document
- Evidence
- StandardizedRecord
- RuleSet
- AuditLog

Tests:
- Model creation
- Constraints
- Relationships
- Migration up/down
- Repository CRUD

---

## GATE-03 — Document Pipeline

Implementation:
- Upload
- File Validation
- Hash
- Storage
- Mock OCR
- Field Extraction
- Normalization

Tests:
- Valid upload
- Invalid type
- Duplicate hash
- OCR result
- Field extraction
- Normalization
- Persistence

---

## GATE-04 — Verification & Anomaly Detection

Implementation:
- V0–V3
- Expiry
- Duplicate
- Conflict
- Missing Field
- Review Queue

Tests:
- V3 / V2 / V1 / V0
- EXPIRED
- DUPLICATE
- CONFLICT
- FUTURE_DATE
- MISSING_REQUIRED_FIELD
- VERIFICATION_FAILED

---

## GATE-05 — Rule Engine

Implementation:
- RuleSet
- Rule Version
- Experience Rules
- Indicator Rules
- Data Health Rules
- Calculation Trace

Tests:
- Rule loading
- Version selection
- Historical preservation
- Calculation trace
- Config validation

---

## GATE-06 — Experience

Implementation:
- Experience Transaction
- Four Dimensions
- Annual Limit
- Total Limit
- Level
- Evidence Link

Tests:
- Base value
- Source recognition
- Dimension limit
- Total limit
- Duplicate protection
- Expiry behavior
- Level boundaries
- Rule version
- Evidence traceability

---

## GATE-07 — Four Indicators

Implementation:
- Completeness
- Credibility
- Business Maturity
- Green Maturity

Each indicator must have independent tests.

---

## GATE-08 — Data Health

Implementation:
- GREEN
- YELLOW
- RED
- GRAY
- Reason
- Action

Mandatory priority tests:

```text
Not Applicable → GRAY
Critical Issue → RED
Minor Issue → YELLOW
Valid Data → GREEN
```

---

## GATE-09 — Farmer Workflow

Implementation:
- Dashboard
- Documents
- Experience
- Indicators
- Data Health
- Tasks

Functional flow:

```text
Farmer Login
→ Upload
→ Process
→ Calculate
→ Dashboard Update
```

---

## GATE-10 — Authorization

Implementation:
- Grant
- Scope
- Expiration
- Revoke

Security tests:

```text
authorized bank → allowed
unauthorized bank → denied
expired authorization → denied
revoked authorization → denied
```

---

## GATE-11 — Bank Workflow

Implementation:
- Case List
- Case Detail
- Indicators
- Data Health
- Evidence

Functional flow:

```text
Bank Login
→ Authorized Case
→ Analysis
→ Evidence
```

---

## GATE-12 — Traceability

Verify:

```text
Result
→ Calculation
→ Rule Version
→ Structured Record
→ Evidence
→ Original Document
```

所有主要計算都必須通過。

---

## GATE-13 — Report

Implementation:
- Bank Information Package

Verify:
- Authorization
- Data correctness
- Rule version
- Evidence references
- Disclaimer
- Generation timestamp

---

## GATE-14 — Full Demo Regression

完整執行：

```text
Farmer
→ Document
→ OCR
→ Normalization
→ Verification
→ Anomaly
→ Data Health
→ Experience
→ Indicators
→ Authorization
→ Bank
→ Evidence
→ Report
```

只有 GATE-14 PASS 才能宣稱 Demo Ready。
