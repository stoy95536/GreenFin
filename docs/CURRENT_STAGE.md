# Current Development Stage

## Repository Status

```text
══════════════════════════════════════════
  ALL 14 GATES PASS — DEMO READY
══════════════════════════════════════════
```

## Completed Gates

| Gate | Name | Status | Date |
|------|------|--------|------|
| BOOTSTRAP-00 | Repository Governance Bootstrap | PASS | 2026-08-17 |
| GATE-01 | Project Foundation | PASS | 2026-08-17 |
| GATE-02 | Core Data Model | PASS | 2026-08-17 |
| GATE-03 | Document Pipeline | PASS | 2026-08-17 |
| GATE-04 | Verification & Anomaly Detection | PASS | 2026-08-17 |
| GATE-05 | Rule Engine | PASS | 2026-08-17 |
| GATE-06 | Experience Calculation | PASS | 2026-08-17 |
| GATE-07 | Four Indicators | PASS | 2026-08-17 |
| GATE-08 | Data Health | PASS | 2026-08-17 |
| GATE-09 | Farmer Workflow | PASS | 2026-08-17 |
| GATE-10 | Authorization | PASS | 2026-08-17 |
| GATE-11 | Bank Workflow | PASS | 2026-08-17 |
| GATE-12 | Traceability | PASS | 2026-08-17 |
| GATE-13 | Report | PASS | 2026-08-17 |
| GATE-14 | Full Demo Regression | PASS | 2026-08-17 |

## Post-GATE-14 — Architecture Hardening (2026-08-17)

An architectural review followed GATE-14. Findings were fixed and re-verified:

| 問題 | 修復 |
|------|------|
| 測試會摧毀正式 Demo 資料（已重現） | 資料目錄改為延遲解析，測試隔離生效 |
| 寫入非原子、有競態 | temp file + os.replace，讀改寫全程持鎖 |
| 四大指標沒讀規則引擎（rule_version 失真） | 權重/門檻全部改由 config 驅動 |
| 必要欄位規則有兩份 | 統一由規則引擎提供 |
| 三份不一致的日期解析 | 統一到 core/dates.py |
| SQLAlchemy/Alembic 死程式碼 + 5 個測試 | 全部移除（ADR-0007） |
| AuditLog 只有模型沒有寫入 | 12 種事件全部實作 + API |
| 前端無型別、銀行頁面繞過 client | 完整型別 + 統一 client |
| Tailwind 從根目錄 build 會沒有樣式 | content globs 錨定設定檔目錄 |
| 無 CI | 新增 GitHub Actions |

決策紀錄：ADR-0007 ~ ADR-0010（見 `docs/DECISIONS.md`）

## Final Statistics

- Total tests: **386** (34 new regression tests, 5 dead tests removed)
- All passing: **Yes**
- Frontend build: **Successful** (strict TypeScript, styles verified present)
- Full demo flow: **Verified end-to-end**
- Live functional verification: **27/27 checks passed**

## Known Limitation

```text
NO AUTHENTICATION
```

`institution_id` 與 `farmer_id` 都是呼叫端提供的路徑參數，因此任何 client 都可以聲稱
自己是任一銀行或小農。授權 guard 驗證的是「授權紀錄是否存在」，不是「呼叫者身分」。

此項經使用者決定暫不實作（Demo 範圍）。對外說明時不得將其描述為已完成的存取控制。

## Demo Proven Capabilities

Per AGENTS.md §5, the demo proves data can be:

```
蒐集 ✓ → 擷取 ✓ → 標準化 ✓ → 核驗 ✓ → 異常檢查 ✓ → 計算 ✓ → 解釋 ✓ → 追溯 ✓ → 授權分享 ✓
```
