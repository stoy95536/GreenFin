# GreenFin 小農綠色數位融資履歷平台

> 目前狀態：Demo / Proof-of-Concept Repository Bootstrap

GreenFin 是一套服務小農與金融機構的「綠色履歷資料治理與授信補充資訊平台」。

它將小農分散的農業經營、交易、綠色行動、驗證與相關證明，經過標準化、來源核驗、資料品質檢查與規則計算後，形成：

- 經驗值
- 四大分析指標
- Data Health
- 可追溯的銀行授信補充資料包

## 重要產品邊界

GreenFin **不是信用評分或自動核貸系統**。

經驗值、四大分析指標與 Data Health 僅作為授信補充資訊，不代表：

- 信用分數
- 核貸機率
- 違約機率
- 額度
- 利率
- 核貸／拒貸建議

最終授信仍由金融機構依正式制度判斷。

## AI 開發者

所有 AI Coding Agent **必須先閱讀 `AGENTS.md`**。

建議啟動指令：

```text
Before making any changes, read AGENTS.md and all documents required by it.

Then inspect:
1. the current repository state,
2. the latest logs/ai-changes records,
3. the latest logs/test-results records,
4. docs/CURRENT_STAGE.md.

Determine the last successfully completed Stage Gate.

Continue only from the next incomplete stage.

Do not skip testing.
Do not modify the repository without creating an AI Change Log.
Do not mark a Stage Gate as PASS unless its required tests were actually executed and passed.
```

## Repository Structure

```text
greenfin/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DOMAIN_MODEL.md
│   ├── RULES.md
│   ├── API_SPEC.md
│   ├── DEMO_SCENARIO.md
│   ├── DEVELOPMENT_PLAN.md
│   ├── CURRENT_STAGE.md
│   ├── DECISIONS.md
│   └── reference/
├── logs/
│   ├── ai-changes/
│   ├── test-results/
│   └── templates/
├── frontend/
├── backend/
├── tests/
└── scripts/
```

## Development Discipline

本專案採：

> Build → Test → Verify → Record → Continue

而不是：

> Build Everything → Test at the End

每個 Gate 完成後必須測試，通過後才可進入下一階段。

## Original References

原始提案與專案文件存於：

`docs/reference/`

這些檔案是規格來源與佐證；實際開發時優先閱讀已整理成 Markdown 的 `docs/` 規格。

## Current Status

請見：

`docs/CURRENT_STAGE.md`

目前 Repository 僅完成專案治理與規格骨架，尚未宣稱任何產品功能已實作。
