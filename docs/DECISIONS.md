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

## ADR-0007 — Remove the Unused SQLAlchemy / Alembic Layer

**Status:** Accepted
**Date:** 2026-08-17
**Supersedes part of:** ADR-0006

**Context:**
ADR-0006 moved persistence to JSON files but kept SQLAlchemy and Alembic "as a future
option". An architecture review found the leftovers were not merely unused but
misleading:

- `core/database.py` had zero runtime consumers; `get_db()` was never injected.
- `alembic/env.py` referenced `Base.metadata`, but the models are Pydantic, so that
  metadata was empty and Alembic could never generate a migration.
- `test_gate01_migration.py` (5 tests) asserted on this dead scaffolding, inflating the
  reported test count with coverage of infrastructure the product does not use.

**Decision:**
Delete `core/database.py`, the entire `alembic/` directory, `alembic.ini`, and the
migration tests. Remove `sqlalchemy`, `alembic`, and `aiosqlite` from requirements.
Remove the `DATABASE_URL` setting, which implied a SQL backend existed.

**Consequences:**
- The dependency list and configuration now describe what the system actually does.
- Test count reflects real product coverage.
- Re-introducing SQL means writing a `SqlRepository` against the existing repository
  interface, which is the swap ADR-0006 was designed for. Nothing about this deletion
  makes that harder.

---

## ADR-0008 — All Indicator Parameters Must Come From the Rule Set

**Status:** Accepted
**Date:** 2026-08-17

**Context:**
The four-indicator calculations hardcoded their tier weights, scoring coefficients and
L1–L5 thresholds while still stamping each `IndicatorResult` with `rule_version`. The
rule engine exposed `get_indicator_rules()`, but only the API endpoint and tests ever
called it. Editing the rule set therefore changed what `/api/rules/active/indicators`
reported without changing a single score, so the recorded provenance was inaccurate and
AGENTS.md §6 (Rule Driven), §7 (rules centralized) and §8 (results tied to a rule
version) were all violated in practice.

The same duplication existed for required fields: `anomaly/detect.py` kept a private
`REQUIRED_FIELDS` constant duplicating `data_health.domain_required_fields`, so the two
services could silently disagree.

**Decision:**
1. `IndicatorRules` carries every number the calculations need: domain→tier mapping,
   tier weights, credibility source scores and penalty/bonus caps, business-maturity
   caps and saturation points, green-maturity caps, and per-indicator level bands.
2. `indicators/calculate.py` contains no numeric business constants. `level_for()` on
   the rule object owns score→level mapping.
3. Anomaly detection reads required fields from the rule engine.
4. `test_regression_rule_driven.py` changes only the config and asserts the scores
   change, so reintroducing hardcoded constants fails the build.

**Consequences:**
- A rule change now genuinely alters results, making `rule_version` meaningful.
- Rule tuning no longer requires touching calculation code.
- Config carries more surface area; the engine supplies GREENFIN_DEMO_V1 defaults so a
  partial config still yields a complete, explicit rule object.

---

## ADR-0009 — Data Directory Resolved Lazily; Writes Are Atomic

**Status:** Accepted
**Date:** 2026-08-17

**Context:**
Two storage defects were found and reproduced:

1. `JsonRepository.__init__` took `data_dir: Path = DATA_DIR`. Python evaluates default
   arguments once at import, so `conftest`'s `monkeypatch` of the module global was a
   no-op and the **entire test suite read and wrote the real `backend/data/`**,
   destroying demo seed data on every run:
   `BEFORE ['GREENFIN_DEMO_V1'] → AFTER ['V1','V2']`.
2. Every mutation was a full read-modify-write using `Path.write_text`, which truncates
   before writing. A crash mid-write truncates the file, and two concurrent writers can
   both read the old list so the second write silently drops the first one's record.

**Decision:**
- Introduce `core/storage.py` as the single owner of data-directory resolution
  (`get_data_dir()` / `set_data_dir()`), resolved at call time. A concrete `Path` must
  never be bound as a default argument or captured by callers.
- Mutations go through `mutate_json_atomic()`, which holds a per-path lock across the
  whole read-modify-write cycle and commits via temp file + `os.replace` (atomic on
  POSIX and Windows).
- Repository construction is side-effect free; files are created on first write.
- `test_regression_data_isolation.py` guards both the outcome (production data
  untouched) and the root cause (no `Path` in `__init__.__defaults__`).

**Consequences:**
- Tests are genuinely isolated; a full suite run leaves seed data intact (verified).
- Readers never observe a partially written file.
- **Limitation stated honestly:** the lock is a `threading.Lock`, so it serialises
  writes within one process only. It does not coordinate multiple uvicorn workers.
  The Demo runs single-process; multi-process safety needs OS-level file locking or a
  real database.

---

## ADR-0010 — Audit Trail Is Written by Services, Not Only Modelled

**Status:** Accepted
**Date:** 2026-08-17

**Context:**
AGENTS.md §32 requires audit entries for 12 product events. The `AuditLog` entity and
repository existed, but no service ever wrote to them — only seed data created two
sample rows. GATE-14 passed without detecting this because no test asserted audit
behaviour. For a product whose value proposition is data governance, a declared but
absent audit trail is a substantive gap.

**Decision:**
- Add `services/audit.py` with one helper per event family and a `get_audit_trail()`
  query, and call it from the document pipeline, verification, anomaly detection, all
  three recalculations, authorization grant/revoke, every bank data read, and report
  generation.
- Audit recording is **best-effort and never raises**: losing a document upload in
  order to protect a log line is the wrong trade-off.
- Denied access is deliberately *not* recorded as `BANK_DATA_ACCESSED`, so the trail
  cannot be misread as "the bank saw this data".
- Expose `GET /api/audit` and `GET /api/audit/event-types`.

**Consequences:**
- A farmer can be shown who accessed their data and when.
- `test_regression_audit_trail.py` asserts each required event actually fires.
- Audit writes add one JSON append per event; acceptable at Demo volume and bounded by
  the same storage limits noted in ADR-0009.
