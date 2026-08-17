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
