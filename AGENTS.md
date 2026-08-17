# AGENTS.md — GreenFin AI Development Guide

> 本檔案是所有 AI Coding Agent 進入本 Repository 後的第一優先閱讀文件。
> 適用於 ChatGPT、Claude Code、Gemini CLI、GitHub Copilot、Cursor 與其他 AI 開發工具。
> 本專案目前定位為 Demo / Proof-of-Concept，不得把模擬成果描述成已商轉或已被金融機構正式採用。

---

## 1. Project Identity

**Project Name:** GreenFin 小農綠色數位融資履歷平台

GreenFin 是一套以資料治理為底座的「綠色履歷資料治理與授信補充資訊平台」。

系統將小農分散於紙本、照片、交易紀錄、農業證明、驗證證書、低碳耕作紀錄、循環利用紀錄、契約、課程及其他經營資料，經過：

```text
原始資料
→ 文件接收
→ OCR / 欄位擷取
→ 資料標準化
→ 來源核驗
→ 效期／重複／矛盾／異常檢查
→ Data Health
→ 經驗值
→ 四大分析指標
→ 小農 Dashboard
→ 授權
→ 銀行 Dashboard
→ 可追溯授信補充資料包
```

形成可驗證、可追溯、可解釋的補充資訊。

---

## 2. Mandatory Reading Order

任何非瑣碎修改前，必須依序閱讀：

1. `AGENTS.md`
2. `docs/PRODUCT_SPEC.md`
3. `docs/RULES.md`
4. `docs/ARCHITECTURE.md`
5. `docs/CURRENT_STAGE.md`

依任務再閱讀：

- API：`docs/API_SPEC.md`
- 資料模型：`docs/DOMAIN_MODEL.md`
- Demo 流程：`docs/DEMO_SCENARIO.md`
- 開發 Gate：`docs/DEVELOPMENT_PLAN.md`
- 架構決策：`docs/DECISIONS.md`

AI 不得只根據既有程式碼猜測業務規則。文件中的正式定義優先於實作方便性。

---

## 3. Core Product Boundary

### GreenFin 不是

- 自動核貸系統
- 信用評分系統
- 違約預測模型
- 貸款媒合平台
- 貸款建議引擎

不得自行建立：

- 信用分數
- 核貸分數
- 核貸／拒貸機率
- 違約機率
- 建議核貸／拒貸
- 建議貸款額度
- 建議貸款利率

GreenFin 僅提供：

> **授信補充資訊**

最終授信仍由金融機構依 KYC、聯徵、還款能力、用途、擔保／信保、財務資料及內部政策完成判斷。

---

## 4. Three Independent Outputs

GreenFin 有三種不同輸出，不得混為單一總分。

### 4.1 經驗值

回答：

> 小農完成多少具有證據、可持續累積的綠色行動？

用途為累積進度、參與回饋與綠色履歷，不是信用分數。

### 4.2 四大分析指標

固定為：

1. 資料完整度
2. 資料可信度
3. 經營成熟度
4. 綠色成熟度

四項指標須獨立呈現，不得直接平均成信用總分。

### 4.3 Data Health

Data Health 是分項底層資料品質的即時診斷，不是第五個績效指標。

狀態：

```text
GREEN
YELLOW
RED
GRAY
```

每個結果至少包含：

```text
status
reason
recommended_action
```

不得只顯示顏色。

---

## 5. Demo Goal

Demo 必須能證明資料可以被：

```text
蒐集
→ 擷取
→ 標準化
→ 核驗
→ 異常檢查
→ 計算
→ 解釋
→ 追溯
→ 授權分享
```

Demo 不需要證明經驗值可預測違約，也不得宣稱銀行一定核貸。

Primary Demo Flow：

```text
Original Document
→ Upload
→ OCR / Extraction
→ Human Confirmation
→ Normalization
→ Source Verification
→ Anomaly Detection
→ Data Health
→ Experience Calculation
→ Four Indicators
→ Farmer Dashboard
→ Authorization
→ Bank Dashboard
→ Evidence Traceability
→ Bank Information Package
```

---

## 6. Architecture Principle

核心原則：

> **Evidence First, Rule Driven, Explainable by Design.**

正確依賴方向：

```text
Evidence
→ Structured Data
→ Verification
→ Rules
→ Calculation
→ Result
```

不得先產生結果再倒推理由。

每個重要結果都必須能回答：

- 為什麼是這個結果？
- 使用哪條規則？
- 使用哪個規則版本？
- 使用哪些結構化欄位？
- 欄位由哪些證據產生？
- 原始文件在哪裡？
- 何時計算？

---

## 7. Business Rule Location

業務規則不得散落於：

- React Components
- API Route Handlers
- Database Models
- HTML / Template

規則應集中於：

```text
backend/app/rules/
backend/app/services/
```

優先採設定檔，例如：

```text
experience_rules_v1.json
indicator_rules_v1.json
data_health_rules_v1.json
```

---

## 8. Rule Versioning

目前 Demo Rule Set：

```text
GREENFIN_DEMO_V1
```

任何計算結果至少保存：

```text
rule_version
calculated_at
input_evidence_ids
calculation_trace
```

規則改版後不得無聲覆蓋歷史計算。

若建立：

```text
GREENFIN_DEMO_V2
```

歷史 V1 結果仍需保留。

---

## 9. Current Demo Experience Rules

四構面：

- 減量
- 增匯
- 循環
- 綠色治理

每構面年度上限：`250`

總上限：`1000`

基礎值：

```text
單次基礎行為 = 20
持續性措施 = 50
正式驗證／重大投入 = 100
```

概念公式：

```text
單筆有效經驗值 = 行為基礎經驗值 × 來源認列比例
```

來源認列比例必須由 Rules Config 取得，不得分散硬寫。

Demo 等級：

```text
L0 尚未建立 = 0
L1 萌芽 = 1–200
L2 成長 = 201–400
L3 穩健 = 401–600
L4 領航 = 601–800
L5 示範 = 801–1000
```

以上均為 Demo 初始參數，不是政府或金融機構標準。

---

## 10. Source Verification Levels

```text
V3 = 官方／合作系統直接核驗
V2 = 可查核第三方文件
V1 = 自行提交且部分佐證
V0 = 無法使用或確認異常
```

每筆 Verification Result 必須保留 reason。

---

## 11. Data Domains

主要資料領域：

```text
IDENTITY
LAND_CROP
TRANSACTION
INPUT_EQUIPMENT
GREEN_ACTION
CERTIFICATION
LOAN_PURPOSE
```

對應：

- 身分與資格
- 土地與作物
- 經營與交易
- 投入與設備
- 綠色行動
- 認證與治理
- 申貸用途

---

## 12. Data Health

至少包含：

```text
IDENTITY_HEALTH
LAND_HEALTH
TRANSACTION_HEALTH
INPUT_HEALTH
GREEN_ESG_HEALTH
LOAN_PURPOSE_HEALTH
```

禁止合成：

- Loan Health Score
- 核貸燈號
- Overall Approval Indicator

判定優先序：

```text
1. 不適用／未授權 → GRAY
2. 重大異常／核心缺件 → RED
3. 一般缺漏／即將到期／待確認 → YELLOW
4. 符合條件 → GREEN
```

RED 不代表拒貸；GRAY 不代表表現差。

---

## 13. Required Anomaly Types

至少支援：

```text
DUPLICATE
EXPIRED
FUTURE_DATE
CONFLICT
INVALID_FORMAT
OCR_LOW_CONFIDENCE
MISSING_REQUIRED_FIELD
VERIFICATION_FAILED
```

可搭配：

```text
INFO
WARNING
CRITICAL
```

異常資料不得直接刪除，應建立 Review Queue 或人工覆核流程。

---

## 14. OCR Architecture

OCR 必須使用 Provider / Adapter 介面，例如：

```python
class OCRProvider:
    def extract(self, file) -> OCRResult:
        ...
```

Demo 至少實作：

```text
MockOCRProvider
```

可預留：

- PaddleOCRProvider
- GoogleVisionProvider
- AzureDocumentIntelligenceProvider
- LLMVisionProvider

業務邏輯不得直接綁定特定 OCR Vendor。

OCR 資料流程：

```text
Raw OCR
→ Extracted Fields
→ Human Confirmation
→ Normalized Fields
```

適用欄位保存：

```text
raw_value
normalized_value
confidence
source
manually_corrected
```

不得丟棄修正歷史。

---

## 15. Frontend / Backend Boundary

Frontend 負責：

- Display
- Interaction
- Validation Feedback
- API Communication

Frontend 不得自行計算：

- 經驗值
- Data Health
- 資料完整度
- 資料可信度
- 經營成熟度
- 綠色成熟度

計算由 Backend Rule Engine 負責。

建議 Backend：

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

建議 Frontend：

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
TanStack Query
React Router
Recharts
Lucide
```

Demo Database 可採 SQLite，但資料設計應相容 PostgreSQL。

---

## 16. Required Entities

至少考慮：

```text
User
FarmerProfile
BankInstitution
Farm
Crop
Document
DocumentField
StandardizedRecord
VerificationResult
Anomaly
GreenAction
ExperienceTransaction
IndicatorResult
DataHealthResult
RuleSet
Authorization
BankCase
AuditLog
```

新增 Entity 前先確認是否可由現有 Entity 表達。

---

## 17. Authorization Boundary

銀行存取必須依賴明確授權。

Authorization 至少包含：

```text
institution
purpose
data_scope
start_at
expire_at
status
revoked_at
```

授權過期或撤回後，Backend 必須拒絕銀行存取，不能只靠前端隱藏。

BANK 可：

- 查看已授權案件
- 查看經驗值／四大指標／Data Health
- 查看異常
- 追溯證據
- 產生授信補充資料包

BANK 不得：

- 修改小農證據
- 修改 GreenFin 計算結果
- 在 GreenFin 內核貸／拒貸

---

## 18. Demo Data Rule

所有虛構資料必須明確標示：

```text
DEMO
SIMULATED
MOCK
```

不得宣稱：

- 真實小農案例
- 真實銀行正式採用
- 正式政府 API 已串接
- 已商轉成功

至少維持三種案例：

### Case A — Healthy
V2/V3、有效資料、多構面綠色行動、GREEN Data Health。

### Case B — Needs Improvement
V1、部分缺漏、即將到期、YELLOW Data Health、補件任務。

### Case C — Abnormal
V0、重複、過期、矛盾、RED Data Health、人工覆核。

---

## 19. Primary Demo Story

虛構案例可使用：

```text
陳小農
綠田友善農場
稻米
```

完整流程：

```text
Farmer Login
→ Dashboard
→ Upload Evidence
→ Mock OCR
→ Confirm Fields
→ Normalize
→ Verify
→ Detect Anomaly
→ Recalculate Data Health
→ Recalculate Experience
→ Recalculate Indicators
→ View Explanation
→ Trace Evidence
→ Authorize Bank
→ Bank Login
→ Open Case
→ Review Analysis
→ Trace Original Evidence
→ Generate Bank Information Package
```

任何破壞此流程的修改都視為 Regression。

---

# 20. Incremental Development and Testing Policy

**嚴禁整個專案全部完成後才第一次測試。**

強制流程：

```text
Requirement
→ Small Development Stage
→ Implementation
→ Automated Test
→ Functional Verification
→ Fix Problems
→ Re-test
→ Record Test Result
→ Stage Gate
→ Next Stage
```

每一階段必須可獨立驗證。

AI 在目前 Stage Gate 未 PASS 前，不得主動進入下一個主要開發階段。

---

## 21. Stage Gate Policy

Stage Gate 必須同時滿足：

```text
Implementation completed
+ Required tests passed
+ Functional verification completed
+ No blocking error
+ AI Change Log written
+ Test Result recorded
= PASS
```

若任一必要條件失敗：

```text
Stage = FAILED / BLOCKED
```

AI 必須：

1. 停止擴張新功能。
2. 找出失敗原因。
3. 修正目前階段。
4. 重跑測試。
5. 記錄失敗與修正。
6. PASS 後才進下一階段。

不得在明知 Gate 失敗的情況下繼續往後堆功能。

---

## 22. Mandatory Development Cycle

每個非瑣碎任務：

### Step 1 — Inspect
- 讀相關文件
- 搜尋現有程式
- 找相依模組
- 找既有測試

### Step 2 — Plan
說明：
- Current objective
- Files expected to change
- Business rules involved
- Tests to add/update
- Verification method

必要假設以：

```text
ASSUMPTION:
```

明確標示。

### Step 3 — Implement
只做目前 Stage 的最小完整變更，不主動把未來 Milestone 一起做掉。

### Step 4 — Develop Tests
測試是實作的一部分，不是最後清理工作。

依功能建立：
- Unit Test
- Integration Test
- API Test
- Component Test
- Functional Test
- Regression Test

### Step 5 — Run Tests
記錄：
- test command
- test scope
- passed
- failed
- warnings

不得宣稱未實際執行的測試已通過。

### Step 6 — Functional Verification
Unit Test 通過不代表功能一定完成。適用時實際驗證：
- API 回傳
- DB Persistence
- Frontend ↔ API
- Authorization
- Calculation Traceability
- Document Pipeline

### Step 7 — Fix and Re-test
流程：

```text
Failure
→ Root Cause
→ Fix
→ Regression Test
→ Re-run
```

不得為了通過測試而刪除有效的失敗測試。

### Step 8 — Record
完成 Stage 前：
- 更新 AI Change Log
- 更新 Test Result
- 更新必要文件

### Step 9 — Gate
回報：

```text
STAGE STATUS: PASS
```

或：

```text
STAGE STATUS: FAILED / BLOCKED
```

只有 PASS 才可進下一 Stage。

---

## 23. GreenFin Development Gates

完整定義請見 `docs/DEVELOPMENT_PLAN.md`。

摘要：

```text
GATE-01 Project Foundation
GATE-02 Core Data Model
GATE-03 Document Pipeline
GATE-04 Verification & Anomaly Detection
GATE-05 Rule Engine
GATE-06 Experience
GATE-07 Four Indicators
GATE-08 Data Health
GATE-09 Farmer Workflow
GATE-10 Authorization
GATE-11 Bank Workflow
GATE-12 Traceability
GATE-13 Report
GATE-14 Full Demo Regression
```

---

# 24. AI Modification Trace Policy

**只要 AI 對 Repository 做任何實際修改，就必須留下可版本控制的修改紀錄。**

包括：

- Create
- Modify
- Delete
- Rename
- Move
- Configuration
- Documentation
- Tests
- Database Schema
- Business Rules
- Dependencies

Git Commit History 不取代本規範。

---

## 25. AI Change Log

目錄：

```text
logs/ai-changes/
```

檔名建議：

```text
YYYY-MM-DD.log
```

例如：

```text
logs/ai-changes/2026-08-17.log
```

規則：

- 必須 Commit 到 Git。
- 採 append-only。
- 不得覆蓋舊紀錄。
- 舊紀錄錯誤時新增 correction entry。
- Timestamp 優先採 Asia/Taipei / UTC+08:00 ISO 8601。

每次修改至少記錄：

```text
Timestamp
Agent
Task
Stage
Status
Summary
Files Created
Files Modified
Files Deleted
Files Renamed / Moved
Database Changes
Business Rule Changes
API Changes
Tests Added
Tests Executed
Test Result
Functional Verification
Known Issues
Next Recommended Step
```

檔案必須逐一列出，不得只寫「updated backend」。

---

## 26. Rule Change Logging

修改任何 GreenFin 規則時額外記錄：

```text
Rule Name
Old Rule Version
New Rule Version
Reason
Affected Calculations
Affected Files
Migration / Recalculation Requirement
```

不得偷偷改分數、門檻或燈號。

---

## 27. Failure Logging

如果失敗嘗試曾修改 Repository 或發現重要技術問題，也需留痕。

記錄：
- Expected
- Actual
- Root Cause
- Fix
- Tests
- Final Result

不得隱藏開發失敗。

---

## 28. Test Evidence Policy

每個 Gate 建議建立：

```text
logs/test-results/gate-XX-*.txt
```

內容至少：

```text
Gate
Timestamp
Test Scope
Commands
Tests Executed
Passed
Failed
Warnings
Functional Verification
Known Issues
Final Gate Status
```

測試結果也要版本控制。

---

## 29. No False Verification

AI 必須區分：

```text
IMPLEMENTED
TESTED
FUNCTIONALLY VERIFIED
NOT VERIFIED
```

若環境無法執行：

```text
IMPLEMENTED
TEST STATUS: NOT EXECUTED
REASON: ...
STAGE STATUS: BLOCKED
```

不得標記 Gate PASS。

---

## 30. Stop-on-Failure

Critical Test 失敗時：

```text
STOP
→ Understand Failure
→ Fix
→ Regression Test
→ Pass Current Gate
```

尤其適用：

- Migration Failure
- Authorization Failure
- Data Loss
- Incorrect Business Calculation
- Rule Version Error
- Evidence Traceability Failure
- Security Boundary Failure
- Broken API Contract

---

## 31. Bug Fix Rule

已確認 Bug 盡可能建立 Regression Test：

```text
Bug Found
→ Reproduce
→ Add Regression Test
→ Confirm Failure
→ Fix
→ Confirm Pass
→ Record Change
```

---

## 32. Audit Trail

重要產品事件應建立 AuditLog，例如：

```text
DOCUMENT_UPLOADED
OCR_COMPLETED
FIELD_CORRECTED
VERIFICATION_UPDATED
ANOMALY_DETECTED
EXPERIENCE_RECALCULATED
INDICATOR_RECALCULATED
DATA_HEALTH_UPDATED
AUTHORIZATION_GRANTED
AUTHORIZATION_REVOKED
BANK_DATA_ACCESSED
REPORT_GENERATED
```

---

## 33. Change Rules

修改前：

```text
Search Repository
→ Identify Existing Implementation
→ Reuse / Extend
```

避免建立：

```text
DashboardNew.tsx
DashboardV2.tsx
DashboardFinal.tsx
DashboardFixed.tsx
```

除非真的需要平行版本。

---

## 34. Coding Standards

鼓勵：

- Clear naming
- Explicit types
- Small cohesive modules
- Pure calculation functions
- Dependency Injection
- Centralized configuration
- Meaningful tests

避免：

- Magic numbers
- Duplicated business rules
- Large route handlers
- Business calculations in React
- Silent fallback
- Untracked rule changes

---

## 35. Assumption Policy

文件沒有正式定義的金融規則，不得自行當成正式規格。

特別是：

- Financial Rules
- Weights
- Thresholds
- Government APIs
- Banking APIs
- Legal Requirements
- Credit Interpretation
- Experience Calculation

需標示：

```text
ASSUMPTION:
目前文件沒有正式定義，以下僅為 Demo Implementation Proposal。
```

---

## 36. Documentation Sync

修改業務規則：
`docs/RULES.md`

修改架構：
`docs/ARCHITECTURE.md`

修改 API：
`docs/API_SPEC.md`

修改 Demo：
`docs/DEMO_SCENARIO.md`

重大架構決策：
`docs/DECISIONS.md`

修改 Gate 狀態：
`docs/CURRENT_STAGE.md`

Code 與 Documentation 不得無聲分歧。

---

## 37. Definition of Stage Done

Stage 完成需符合適用項目：

```text
[ ] Requirement implemented
[ ] Unit tests created
[ ] Integration tests created where applicable
[ ] Regression tests executed
[ ] Tests passed
[ ] Functional verification completed
[ ] Error states checked
[ ] Authorization checked where relevant
[ ] Traceability checked where relevant
[ ] Documentation updated
[ ] AI Change Log updated
[ ] Test Result record updated
[ ] No blocking issue remains
```

才可：

```text
STAGE STATUS = PASS
```

---

## 38. Final Development Rule

GreenFin 強制遵循：

> **Build → Test → Verify → Record → Continue**

禁止：

> **Build Everything → Test at the End**

每次 AI 修改都必須能回答：

- What changed?
- When?
- Why?
- Which files?
- Which tests?
- Did tests pass?
- Which Gate?
- What next?

若無法回答，修改紀錄即不完整。
