# GreenFin Demo API Specification

> 本文件為初始 API 草案。GATE-01～GATE-02 後可依實際 Domain Model 調整，但調整需同步記錄。

## Suggested Endpoints

```text
POST   /api/auth/login

GET    /api/farmers/me
GET    /api/farmers/me/dashboard

GET    /api/documents
POST   /api/documents
GET    /api/documents/{id}
POST   /api/documents/{id}/process
PATCH  /api/documents/{id}/fields/{field_id}

GET    /api/experience
GET    /api/experience/transactions

GET    /api/indicators
GET    /api/indicators/{indicator}

GET    /api/data-health
GET    /api/tasks

GET    /api/authorizations
POST   /api/authorizations
POST   /api/authorizations/{id}/revoke

GET    /api/bank/cases
GET    /api/bank/cases/{id}
GET    /api/bank/cases/{id}/evidence
GET    /api/bank/cases/{id}/report

GET    /api/audit
```

## Response Envelope

Success:

```json
{
  "success": true,
  "data": {},
  "meta": {},
  "error": null
}
```

Error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "找不到指定文件"
  }
}
```

## Authorization Requirement

銀行 API 必須在 Backend 檢查：
- Institution
- Data Scope
- Start / Expiry
- Revocation Status

不得只依 Frontend 控制。
