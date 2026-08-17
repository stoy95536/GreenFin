# GreenFin 安裝與操作指南

## 系統需求

- Python 3.11+
- Node.js 18+
- npm 9+

---

## 安裝

### 後端

```bash
cd c:\Users\USER\Documents\Code\GreenFin\GreenFin
pip install -r backend/requirements.txt
```

主要依賴：FastAPI, Pydantic, uvicorn

### 前端

```bash
cd frontend
npm install
```

主要依賴：React, TypeScript, Vite, Tailwind CSS, React Router, Lucide

---

## 啟動

### 1. 載入 Demo 種子資料

```bash
python -m backend.app.seed.seed_data
```

這會在 `backend/data/` 建立 18 個 JSON 檔案，包含三個 Demo 小農案例。

### 2. 啟動後端 API Server

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

後端啟動後可測試：http://127.0.0.1:8000/api/health

### 3. 啟動前端開發伺服器

另開一個終端：

```bash
cd frontend
npm run dev
```

瀏覽器打開：http://localhost:5173

---

## 操作流程

### 小農端

1. 右上角下拉選單切換小農（陳小農 / 林阿花 / 王大明）
2. **Dashboard** — 總覽經驗值、指標、Data Health
3. **文件管理** — 上傳文件，選擇資料領域，觸發 OCR，確認欄位，處理管線
4. **經驗值** — 查看各構面累積與計算歷史
5. **四大指標** — 查看獨立分數（點「重新計算」觸發）
6. **Data Health** — 查看各資料領域健康狀態

### 首次使用

第一次進入 Dashboard 時各項數值可能為 0 或空白，需點「**重新計算**」按鈕觸發後端計算。

---

## API 文件

啟動後端後，自動生成的 API 文件：

- Swagger UI：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc

### 主要 API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /api/health | 系統健康檢查 |
| POST | /api/documents/upload | 上傳文件 |
| GET | /api/documents/{id} | 取得文件詳情 |
| POST | /api/documents/{id}/confirm | 確認 OCR 欄位 |
| POST | /api/documents/{id}/normalize | 標準化 |
| POST | /api/documents/{id}/verify | 核驗 + 異常偵測 |
| GET | /api/farmers/{id}/documents | 小農文件列表 |
| GET | /api/farmers/{id}/experience | 經驗值摘要 |
| POST | /api/farmers/{id}/experience/recalculate | 重算經驗值 |
| GET | /api/farmers/{id}/indicators | 四大指標 |
| POST | /api/farmers/{id}/indicators/calculate | 計算指標 |
| GET | /api/farmers/{id}/data-health | Data Health |
| POST | /api/farmers/{id}/data-health/calculate | 計算 Data Health |
| GET | /api/farmers/{id}/anomalies | 異常清單 |
| GET | /api/farmers/{id}/review-queue | 待覆核項目 |
| GET | /api/rules/active | 當前規則版本 |
| GET | /api/rules/active/experience | 經驗值規則 |
| POST | /api/authorizations/grant | 建立授權 |
| POST | /api/authorizations/{id}/revoke | 撤回授權 |
| GET | /api/bank/{id}/farmer/{id}/data | 銀行存取（需授權）|

---

## 測試

```bash
cd c:\Users\USER\Documents\Code\GreenFin\GreenFin
python -m pytest backend/tests/ tests/ -q
```

目前共 310 個測試。

---

## 專案結構

```
GreenFin/
├── AGENTS.md              # AI 開發規範
├── README.md              # 專案說明（本檔案連結）
├── SETUP.md               # 安裝與操作指南（本檔案）
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI 路由
│   │   ├── core/          # 設定、資料庫
│   │   ├── models/        # Pydantic 領域模型
│   │   ├── repositories/  # JSON 檔案 Repository
│   │   ├── rules/         # 規則引擎
│   │   ├── seed/          # Demo 種子資料
│   │   └── services/      # 業務邏輯
│   │       ├── anomaly/
│   │       ├── authorization/
│   │       ├── data_health/
│   │       ├── documents/
│   │       ├── experience/
│   │       ├── indicators/
│   │       ├── normalization/
│   │       ├── ocr/
│   │       ├── reports/
│   │       └── verification/
│   ├── data/              # JSON 資料儲存
│   ├── tests/             # 後端測試
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.ts         # API 客戶端
│   │   ├── components/    # 共用元件
│   │   ├── context/       # React Context (小農切換)
│   │   └── pages/         # 頁面元件
│   ├── package.json
│   └── vite.config.ts
├── docs/                  # 規格文件
├── logs/                  # AI 修改紀錄 + 測試結果
└── scripts/               # 工具腳本
```

---

## Demo 三案例說明

### Case A — 陳小農（Healthy）
- 有機認證（V3）、農會出貨單（V2）
- 經驗值：150（減量構面）
- Data Health：多數 GREEN
- 代表：資料完整且經核驗的小農

### Case B — 林阿花（Needs Improvement）
- 僅有照片佐證（V1）
- 經驗值：10（循環構面，V1 半認列）
- Data Health：多數 YELLOW
- 代表：需要補強資料的小農

### Case C — 王大明（Abnormal）
- 過期文件（V0）、重複上傳
- 經驗值：0（V0 不認列）
- Data Health：多數 RED
- 代表：資料有重大問題需覆核的小農

---

## 注意事項

- 所有資料皆為 **DEMO / SIMULATED**，不代表真實案例
- 經驗值、指標、Data Health 僅為授信補充資訊
- RED 不代表拒貸，GRAY 不代表表現差
- 本專案不做核貸、信用評分或違約預測
