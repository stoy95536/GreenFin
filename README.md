# GreenFin 小農綠色數位融資履歷平台

GreenFin 是一套服務小農與金融機構的**綠色履歷資料治理與授信補充資訊平台**。

它將小農分散的農業經營、交易、綠色行動、驗證與相關證明，經過標準化、來源核驗、資料品質檢查與規則計算後，形成可追溯、可解釋的授信補充資訊。

> 目前狀態：Demo / Proof-of-Concept（已完成 GATE-01 ~ GATE-10）

---

## 核心功能

| 功能 | 說明 |
|------|------|
| 文件上傳與 OCR | 上傳證據文件，自動擷取欄位，人工確認後標準化 |
| 來源核驗 | 判定 V0~V3 來源強度，偵測 8 種異常 |
| 經驗值 | 四構面綠色行動累積（減量/增匯/循環/綠色治理） |
| 四大分析指標 | 資料完整度、可信度、經營成熟度、綠色成熟度（獨立呈現） |
| Data Health | 七大資料領域即時診斷（GREEN/YELLOW/RED/GRAY） |
| 授權機制 | 小農授權銀行存取，過期/撤回即拒絕 |
| 小農 Dashboard | 完整的操作介面，可切換三種 Demo 案例 |

## 重要產品邊界

GreenFin **不是信用評分或自動核貸系統**。所有產出僅為授信補充資訊，最終授信仍由金融機構依正式制度判斷。

---

## 快速啟動

```bash
# 1. 安裝後端依賴
pip install -r backend/requirements.txt

# 2. 安裝前端依賴
cd frontend && npm install && cd ..

# 3. 載入 Demo 種子資料
python -m backend.app.seed.seed_data

# 4. 啟動後端 API
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 5. 啟動前端（另一個終端）
cd frontend && npm run dev
```

瀏覽器打開 http://localhost:5173

---

## Demo 案例

| 案例 | 小農 | 農場 | 狀態 |
|------|------|------|------|
| Case A | 陳小農 | 綠田友善農場 | Healthy — GREEN |
| Case B | 林阿花 | 日出有機園 | Needs Improvement — YELLOW |
| Case C | 王大明 | 舊園地 | Abnormal — RED |

右上角下拉選單可切換小農查看不同情境。

---

## 技術架構

| 層 | 技術 |
|----|------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Lucide |
| Backend | Python + FastAPI + Pydantic |
| Storage | JSON 檔案（Demo 用，設計相容 PostgreSQL） |
| 規則引擎 | 版本化 JSON 規則設定，可追溯計算 |

---

## 專案文件

| 文件 | 說明 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI 開發者必讀，開發規範與治理政策 |
| [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | 產品規格 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架構設計 |
| [docs/RULES.md](docs/RULES.md) | 業務規則（經驗值/指標/Data Health） |
| [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | 14 個 Gate 開發計畫 |
| [docs/CURRENT_STAGE.md](docs/CURRENT_STAGE.md) | 當前開發進度 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | 架構決策紀錄 |
| [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md) | 領域模型 |
| [docs/API_SPEC.md](docs/API_SPEC.md) | API 規格 |
| [docs/DEMO_SCENARIO.md](docs/DEMO_SCENARIO.md) | Demo 流程情境 |
| [SETUP.md](SETUP.md) | 完整安裝與操作指南 |

---

## 開發紀律

本專案強制遵循：

> **Build → Test → Verify → Record → Continue**

每個 Gate 必須測試通過後才進下一階段。所有修改皆留 AI Change Log。

詳見 [AGENTS.md](AGENTS.md)。

---

## 當前狀態

GATE-01 ~ GATE-10 已完成（310 個測試全部通過）。

詳見 [docs/CURRENT_STAGE.md](docs/CURRENT_STAGE.md)。
