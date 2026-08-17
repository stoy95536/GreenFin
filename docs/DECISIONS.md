# Architecture / Product Decision Log

## ADR-0001 — Use AGENTS.md as AI Entry Point

**Status:** Accepted

所有 AI Coding Agent 進入 Repository 後先讀 `AGENTS.md`，再依其 Mandatory Reading Order 載入正式規格。

## ADR-0002 — Incremental Stage Gate Development

**Status:** Accepted

採 Build → Test → Verify → Record → Continue。

禁止整體完成後才首次測試。

## ADR-0003 — AI Modifications Must Leave Repository Trace

**Status:** Accepted

任何 AI 實際修改都必須寫入 `logs/ai-changes/`，且修改檔案逐一列出。

Git commit 不取代 AI Change Log。

## ADR-0004 — Evidence First, Rule Driven, Explainable by Design

**Status:** Accepted

所有重要結果必須可追溯 Rule Version、Structured Data 與 Original Evidence。

## ADR-0005 — GreenFin Does Not Make Lending Decisions

**Status:** Accepted

經驗值、四大分析指標與 Data Health 僅為授信補充資訊，不得合成核貸分數或自動核貸結果。

## ADR-0006 — Demo Storage: JSON Files Instead of SQL Database

**Status:** Accepted  
**Date:** 2026-08-17  
**Context:** GATE-02 開始時，由使用者決定 Demo 不需要 SQL 資料庫。

**Decision:**
- 資料儲存使用 JSON 檔案（每個 Entity 類型一個 `.json`），存放於 `backend/data/` 目錄
- 保留 Pydantic models 做資料驗證與型別定義
- Repository 層封裝所有讀寫邏輯，介面不變，未來可替換為 SQL 實作
- SQLAlchemy / Alembic 設定保留但不作為主要資料路徑
- Health endpoint 改為檢查 data 目錄是否可存取

**Consequences:**
- 優點：啟動零門檻、資料可直接用文字編輯器檢視、Demo 簡潔
- 缺點：無交易保護、併發寫入需自行處理（Demo 不需要）、查詢效能有限
- 風險：可接受，因為 Demo 資料量小且為單人操作

**Migration Path:**
Repository interface 不變 → 未來 GATE 若需切換 PostgreSQL，只需新增 SQLRepository 實作並注入。
