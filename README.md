# GreenFin 小農綠色數位融資履歷平台

GreenFin 是一套服務小農與金融機構的**綠色履歷資料治理與授信補充資訊平台**。

它將小農分散的農業經營、交易、綠色行動、驗證與相關證明，經過標準化、來源核驗、資料品質檢查與規則計算後，形成可追溯、可解釋的授信補充資訊，協助銀行在傳統財務報表以外更完整地理解小農的經營表現。

---

## 產品定位

GreenFin **不是**信用評分、自動核貸或違約預測系統。

平台產出的經驗值、四大分析指標與 Data Health 僅作為**授信補充資訊**，最終授信仍由金融機構依正式制度判斷。

---

## 核心功能

### 資料治理管線

| 階段 | 功能 |
|------|------|
| 蒐集 | 小農透過平台上傳各類證據文件（PDF、照片、報表） |
| 擷取 | OCR 自動辨識文件內容，擷取結構化欄位 |
| 確認 | 人工確認 / 修正 OCR 結果 |
| 標準化 | 日期、金額、面積等格式自動正規化 |
| 核驗 | 判定來源強度 V0–V3（官方核驗 → 自行提交） |
| 異常偵測 | 自動偵測 8 種異常（過期、重複、矛盾、格式錯誤等） |

### 分析輸出（三大獨立產出）

| 產出 | 說明 |
|------|------|
| **經驗值** | 四構面（減量/增匯/循環/綠色治理）綠色行動累積，不是信用分數 |
| **四大分析指標** | 資料完整度、可信度、經營成熟度、綠色成熟度（獨立呈現，不合併） |
| **Data Health** | 七大資料領域的即時品質診斷（GREEN/YELLOW/RED/GRAY） |

### 授權與銀行端

- 小農控制資料授權（選銀行、選範圍、設期限）
- 授權過期或撤回 → 後端拒絕存取（不只是前端隱藏）
- 銀行端可查看授權案件、追溯證據、產生授信補充資料包

### 稽核軌跡

所有重要事件（上傳、核驗、異常偵測、計算、授權、銀行存取、報告產出）皆自動記錄稽核日誌。

---

## 系統架構

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite + Tailwind CSS)     │
│  ─ 小農 Dashboard / 文件管理 / 經驗值 / 指標 / Data Health │
│  ─ 銀行端：案件列表 / 分析檢視 / 證據追溯               │
│  ─ 登入 / 註冊 / 權限區分                               │
└────────────────────────┬────────────────────────────────┘
                         │ Vite Proxy (/api)
┌────────────────────────▼────────────────────────────────┐
│  Backend (Python + FastAPI + Pydantic)                    │
│  ─ 文件管線 (Upload → OCR → Confirm → Normalize → Verify)│
│  ─ 規則引擎 (版本化、可追溯計算)                         │
│  ─ 經驗值 / 指標 / Data Health 計算服務                  │
│  ─ 授權 Guard (後端強制)                                 │
│  ─ 稽核軌跡                                             │
│  ─ 銀行資料包產生                                        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Storage (JSON 檔案，Repository 模式封裝)                │
│  ─ 可替換為 PostgreSQL，業務層零依賴儲存細節             │
└─────────────────────────────────────────────────────────┘
```

### 設計原則

> **Evidence First, Rule Driven, Explainable by Design.**

- 每個結果可追溯到：使用哪條規則 → 哪個規則版本 → 哪些結構化欄位 → 哪份原始文件
- 規則版本化，歷史計算不被覆蓋
- 改規則設定會改計算結果（有測試證明）

---

## 快速啟動

### 環境需求

- Python 3.11+
- Node.js 18+

### 安裝

```bash
# 後端
pip install -r backend/requirements.txt

# 前端
cd frontend && npm install && cd ..
```

### 啟動

```bash
# 1. 載入 Demo 種子資料
python -m backend.app.seed.seed_data

# 2. 啟動後端
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 3. 啟動前端（另一個終端）
cd frontend && npm run dev
```

瀏覽器打開 **http://localhost:5173**

---

## Demo 操作流程

### 登入

首頁是登入頁，提供 5 個預建帳號（Demo 模式免密碼）：

| 帳號 | 角色 | 說明 |
|------|------|------|
| 陳小農 | 小農 | 資料完整的健康案例 |
| 林阿花 | 小農 | 資料不足需補強的案例 |
| 王大明 | 小農 | 資料異常需覆核的案例 |
| 台新銀行審查員 | 銀行 | 銀行端視角 |
| 系統管理員 | 管理員 | 可切換查看所有小農 |

也可點「註冊新帳號」建立新小農。

### 小農操作

1. **登入** → 進入 Dashboard
2. **綠色行動** → 新增行動（選構面、等級、填描述）
3. **文件管理** → 上傳文件 → 看 OCR 結果 → 按「處理」完成管線
4. **Dashboard** → 按「重新計算」→ 看到經驗值、指標、Data Health 即時更新
5. **授權銀行**（透過 API）

### 銀行操作

1. 用「台新銀行審查員」登入
2. 看到已授權的小農案件
3. 點進案件 → 查看經驗值、四大指標、Data Health、異常
4. 點「證據追溯」→ 看到完整 Document → Fields → Records → Verification 鏈路

### 管理員

- 登入後進入與小農相同的介面
- 右上角出現下拉選單，可切換查看任何小農的資料

---

## Demo 案例

三個預建案例展示不同資料品質情境：

| 案例 | 小農 | 農場 | 資料狀態 |
|------|------|------|----------|
| Case A | 陳小農 | 綠田友善農場 | 完整、V2/V3 來源、GREEN |
| Case B | 林阿花 | 日出有機園 | 部分缺漏、V1 來源、YELLOW |
| Case C | 王大明 | 舊園地 | 過期/重複/異常、V0、RED |

---

## 專案結構

```
GreenFin/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI 路由端點
│   │   ├── core/          # 設定、儲存原語、日期工具
│   │   ├── models/        # Pydantic 領域模型 (18 Entity + 12 Enum)
│   │   ├── repositories/  # Repository 模式 (JSON 實作，可替換)
│   │   ├── rules/         # 規則引擎 (版本化設定 + 型別存取)
│   │   ├── seed/          # Demo 種子資料
│   │   └── services/      # 業務邏輯
│   │       ├── anomaly/       # 8 種異常偵測
│   │       ├── authorization/ # 授權 + 存取 Guard
│   │       ├── data_health/   # Data Health 計算
│   │       ├── documents/     # 上傳 + OCR + 標準化
│   │       ├── experience/    # 經驗值計算
│   │       ├── indicators/    # 四大指標計算
│   │       ├── ocr/           # OCR Provider 介面 (Mock + 可替換)
│   │       ├── reports/       # 銀行資料包產生
│   │       └── verification/  # 來源核驗 V0-V3
│   ├── data/              # JSON 資料儲存
│   └── tests/             # 386 個後端測試
├── frontend/
│   ├── src/
│   │   ├── api.ts         # Typed API Client
│   │   ├── types.ts       # 完整型別定義
│   │   ├── context/       # Auth + Farmer Context
│   │   ├── components/    # Layout 元件
│   │   └── pages/         # 頁面元件
│   │       ├── Login / Register
│   │       ├── Dashboard / Documents / Experience
│   │       ├── Indicators / DataHealth / GreenActions
│   │       └── bank/ (Cases / CaseDetail / Evidence)
│   └── package.json
├── docs/                  # 規格文件
├── logs/                  # AI 修改紀錄 + 測試結果
├── .github/workflows/     # CI (GitHub Actions)
└── AGENTS.md              # AI 開發規範
```

---

## 未來替換路徑

本系統設計為 Demo / PoC，但架構已預留真實部署的替換點：

| 現在（Demo） | 未來（正式） | 替換範圍 |
|---|---|---|
| JSON 檔案儲存 | PostgreSQL | 只改 `repositories/` 層 |
| MockOCRProvider | PaddleOCR / Google Vision / Azure | 只改 `services/ocr/` |
| Demo 規則參數 | 校準後的正式參數 | 只改 JSON 設定檔 |
| 免密碼登入 | OAuth2 / JWT | 加 middleware |
| 單 process | 多 worker + Redis lock | 替換 storage lock |

業務邏輯層（services）**不需要修改**即可完成上述替換。

---

## API 文件

啟動後端後，自動產生的互動式文件：
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## 測試

```bash
python -m pytest backend/tests/ tests/ -q
```

目前 386 個測試涵蓋：
- 文件管線（上傳、OCR、標準化、核驗）
- 規則引擎（版本選擇、設定驅動計算）
- 經驗值（公式、限額、等級、重複保護）
- 四大指標（獨立計算、規則驅動有測試證明）
- Data Health（優先序邏輯、7 領域）
- 授權（授權/過期/撤回 → 403）
- 追溯（完整鏈路驗證）
- 資料隔離（測試不會破壞正式 Demo 資料）
- 稽核軌跡（12 種事件皆有寫入且可查詢）

---

## 規格文件

| 文件 | 說明 |
|------|------|
| [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | 產品規格 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架構設計 |
| [docs/RULES.md](docs/RULES.md) | 業務規則 |
| [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md) | 領域模型 |
| [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | 14 Gate 開發計畫 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | 架構決策紀錄 (ADR) |
| [docs/CURRENT_STAGE.md](docs/CURRENT_STAGE.md) | 當前開發狀態 |
| [SETUP.md](SETUP.md) | 完整安裝與操作指南 |

---

## 授權聲明

本專案目前為 Demo / Proof-of-Concept 階段。所有資料均為模擬，不代表真實案例、真實銀行合作或已商轉。
