# High-Level Design Review: GenHealth AI DME Order Management

**Document Reviewed:** `design/assessment-high-level-design.md`
**Requirements Reference:** `design/assessment-requirements.md`
**Review Date:** 2026-04-08
**Reviewer:** Claude (Automated Review)

---

## Executive Summary

The high-level design is well-structured with clear component boundaries, solid decision rationale, and comprehensive security coverage for an assessment MVP. The most critical gaps are: a missing error storage field in the Order data model (blocking FR-3.3.4), an unresolved contradiction between synchronous extraction and references to "polling" in the frontend, and an undecided refresh token strategy that affects whether logout works. The design is close to ready for low-level design but needs targeted fixes in a few areas.

**Overall Verdict:** Needs targeted fixes before proceeding

---

## Section Verdicts

| Review Area | Verdict | Findings |
|-------------|---------|----------|
| Architecture & Component Design | Sufficient | 3 |
| Data Model Soundness | Partially Addressed | 4 |
| Data Flow Integrity | Partially Addressed | 4 |
| Security Architecture | Sufficient | 4 |
| Technology Choices | Partially Addressed | 3 |
| Deployment & Operational Readiness | Partially Addressed | 4 |
| Requirements Coverage | Sufficient | 3 |
| Specification Clarity | Partially Addressed | 4 |

---

## 1. Architecture & Component Design

### Current State

The design describes a monolithic Flask application serving both the API and React frontend, with clear subcomponent tables for each major component. Communication patterns are straightforward (synchronous HTTP, local filesystem, outbound HTTPS to Claude). The monolith decision is well-justified for the assessment scope.

### Strengths

- Monolith justification is thorough with concrete rationale and alternatives considered
- Subcomponent responsibility tables clearly define ownership boundaries
- The URL routing strategy (Section 6.7) explicitly addresses how API routes coexist with the SPA catch-all
- Single deployment unit rationale is sound for the assessment context

### Gaps and Recommendations

| ID | Gap | Priority | Recommendation |
|----|-----|----------|----------------|
| ARCH-1 | Gunicorn is absent from the architecture diagram (Section 2) despite being a critical component between Azure TLS and Flask. Multiple workers introduce concurrency considerations for SQLite. | Consider | Add Gunicorn as an explicit node in the architecture diagram. Show the worker model (multiple processes sharing one SQLite file) to make the concurrency constraint visible. |
| ARCH-2 | The architecture flow shows Router → AuthMW → LogMW → Services, implying logging happens after auth. However, the activity logging middleware uses `after_request` (Section 5.5) which fires for all responses. The diagram is misleading about when logging occurs relative to auth failures. | Consider | Clarify in the architecture diagram or prose that `after_request` logging captures all requests regardless of auth outcome, including 401s. The current flow arrow ordering suggests logging only happens for authenticated requests. |
| ARCH-3 | No mention of how the SPA catch-all route interacts with API 404 responses. If a user hits `/api/v1/nonexistent`, does Flask return an API-style JSON 404 or the SPA's `index.html`? | Should Address | Define the route precedence: API blueprints handle `/api/*` (returning JSON errors for unknown routes within this prefix), and non-API paths fall through to the SPA catch-all. This needs explicit specification to avoid ambiguity during implementation. |

### Verdict: **Sufficient**

---

## 2. Data Model Soundness

### Current State

Four entities (User, Order, Document, ActivityLog) are defined with full attribute lists, cardinalities, and a lifecycle description. The ER diagram uses correct notation and the state machine is clear.

### Strengths

- All entities from requirements are present with detailed attributes
- Cardinalities are correct: User 1-to-many Orders, Order 0-or-1 Document, User 1-to-many ActivityLogs
- Data lifecycle section explicitly covers create/update/delete semantics for each entity
- State machine covers all transitions including retry (failed → processing)

### Gaps and Recommendations

| ID | Gap | Affected Entity | Priority | Recommendation |
|----|-----|-----------------|----------|----------------|
| DATA-1 | Order entity has no field to store error descriptions when extraction fails. FR-3.3.4 states: "System SHALL transition the order status to `failed` if extraction fails, **with an error description stored**." There is no `error_message` or `error_detail` attribute on Order. | Order | Must Address | Add an `error_message` (text, nullable) field to the Order entity. This stores the sanitized extraction failure reason visible to the user and drives the frontend's error display on failed orders. |
| DATA-2 | The `role` field exists on User but the authorization model (Section 7.1) says "All authenticated users have equal access (no role-based restrictions in v1)." The field is in the JWT payload per FR-3.1.2. This creates ambiguity: is `role` populated? With what value? Is it validated? | User | Should Address | Either (a) remove `role` from the v1 data model and JWT payload since it's not used, or (b) specify a default value (e.g., `"user"`) and document that role-based enforcement is deferred but the field is present for forward compatibility. Option (b) is recommended. |
| DATA-3 | Document stores `extracted_data` as JSON and Order stores individual extracted fields (patient_first_name, insurance_provider, etc.). The relationship between these is unclear — is `extracted_data` the raw LLM response and Order fields the validated/parsed version? What is the source of truth if they diverge? | Document, Order | Should Address | Clarify the data flow: `extracted_data` on Document is the raw LLM JSON response (archival/debugging), and individual Order fields are the validated, persisted values (source of truth for the application). Document this distinction in the data model section. |
| DATA-4 | Requirements NFR-6.2 specifies indexes on `status`, `created_at`, and `patient_last_name`. No indexes are mentioned in the data model. While index design is partly implementation-level, key indexes affect query performance architecture. | Order | Consider | Note which columns require indexes in the data model section. For SQLite, this is especially relevant because poor indexing can cause full table scans that block the single writer. |

### Verdict: **Partially Addressed**

---

## 3. Data Flow Integrity

### Current State

Five data flows are documented: registration/login, order CRUD, document upload/extraction (happy path), extraction failure path, and activity logging. The extraction failure flowchart is notably thorough with multiple decision points.

### Strengths

- The extraction failure path (Section 5.4) is excellent — covers text extraction failure, Claude timeout/5xx, rate limiting, schema validation, and missing required fields
- Activity logging flow correctly shows non-blocking behavior
- Sequence diagrams clearly identify which component initiates, processes, and persists

### Gaps and Recommendations

| ID | Gap | Flow | Priority | Recommendation |
|----|-----|------|----------|----------------|
| FLOW-1 | Token refresh flow is not documented. FR-3.1.3 specifies a refresh mechanism, and there is a `POST /api/v1/auth/refresh` endpoint in the requirements. The refresh flow has different auth requirements (refresh token vs. access token) and different behavior. | Token Refresh | Should Address | Add a sequence diagram showing: client sends expired-access-token request, gets 401, client sends refresh token to `/auth/refresh`, receives new access token. This flow is critical for understanding client-side token management. |
| FLOW-2 | Order deletion cascade flow is not documented. FR-3.2.5 requires cascade-deleting Document records, but what about the physical PDF file on disk? If the file isn't deleted, orphaned files accumulate on the Azure filesystem. | Order Deletion | Should Address | Add a data flow showing: delete order → delete Document DB record → delete physical PDF file from filesystem (or mark for cleanup). This affects storage management on Azure App Service. |
| FLOW-3 | The frontend component table (Section 3.2) mentions "extraction status polling" for the Document Upload subcomponent, but Section 6.3 explicitly chooses synchronous extraction. These contradict — if extraction is synchronous, the client simply waits for the HTTP response, no polling is needed. | Document Upload | Must Address | Resolve the contradiction. If synchronous: remove "polling" references and clarify that the frontend shows a loading state during the long HTTP request. If polling is desired: that contradicts the synchronous decision and would require an async architecture. |
| FLOW-4 | No data flow for admin activity log retrieval (`GET /api/v1/admin/activity-logs`). While simple, it's the only endpoint with different access semantics (the requirements suggest pagination, filtering by user/endpoint/date). | Activity Log Retrieval | Consider | Add a brief flow or note clarifying whether this endpoint has any special auth requirements (admin-only?) or if any authenticated user can access it. The requirements say "admin endpoint" but v1 has no roles. |

### Verdict: **Partially Addressed**

---

## 4. Security Architecture

### Current State

| Aspect | Status | Notes |
|--------|--------|-------|
| Authentication | Defined | JWT with bcrypt password hashing, clear flow diagram |
| Authorization | Defined | Flat model (all equal). Simple but explicit. |
| Trust Boundaries | Defined | Diagram showing public/edge/app/external boundaries |
| Encryption in Transit | Defined | Azure TLS termination, HTTPS to Claude |
| Encryption at Rest | Partial | SQLite file on Azure persistent storage — no explicit encryption |
| Secrets Management | Defined | Environment variables, not in source control |
| Input Validation | Defined | Threat/mitigation table covering OWASP top risks |

### Strengths

- Trust boundary diagram is clear and correctly identifies all boundaries
- Data protection table covers every category of sensitive data
- HIPAA disclaimer is prominent in both the overview and a dedicated section
- Input validation table covers SQL injection, XSS, CSRF, file uploads, brute force, and path traversal

### Gaps and Recommendations

| ID | Gap | Priority | Recommendation |
|----|-----|----------|----------------|
| SEC-1 | JWT uses HS256 (symmetric signing). The design doesn't note the security implication: anyone with the `JWT_SECRET_KEY` can forge tokens. For a single-service monolith this is acceptable, but should be explicitly acknowledged since the key is the single point of compromise for all authentication. | Consider | Add a brief note to Section 7.1: "HS256 is acceptable for a single-service architecture where the signing key never leaves the server. If the system evolves to multiple services verifying tokens, RS256 (asymmetric) SHOULD be adopted." |
| SEC-2 | No JWT revocation mechanism. If a user needs to be locked out or changes their password, existing tokens remain valid until expiry (up to 60 min for access, 7 days for refresh). Open Question #6 about refresh token storage directly impacts this security property. | Should Address | Decide on refresh token strategy before proceeding. Recommendation: store refresh tokens in the database so they can be revoked. Access token short-livedness (60 min) limits the blast radius. Document that immediate access token revocation is deferred to v2 (would require a token blacklist). |
| SEC-3 | The LLM extraction endpoint (`POST /api/v1/orders/{id}/upload`) is expensive (Anthropic API costs, 10-30s compute time) but only auth endpoints are rate-limited. A malicious authenticated user could trigger many concurrent extraction requests, causing API cost spikes and resource exhaustion. | Should Address | Add rate limiting to the upload/extraction endpoint. Recommendation: per-user rate limit of N extraction requests per minute via Flask-Limiter. Document in the security architecture that LLM-calling endpoints have separate rate limits. |
| SEC-4 | No mention of PDF-specific attack vectors. Malformed PDFs can crash parsing libraries (denial of service) or exploit parser vulnerabilities. Only MIME type and file size are validated. | Consider | Note in Section 7.4 that the PDF parser SHOULD run with error handling that catches and gracefully handles malformed PDF exceptions. Consider running PDF parsing in a try/except that sets the order to `failed` if the parser crashes, preventing application-wide impact. |

### Verdict: **Sufficient**

---

## 5. Technology Choices

### Assessment

| Technology | Choice | Rationale Provided? | Alternatives Considered? | Concerns |
|------------|--------|---------------------|--------------------------|----------|
| Backend language | Python 3.11+ | Yes | N/A (assessment requirement) | None |
| Web framework | Flask | Yes | Yes (FastAPI, Django) | None |
| ORM | SQLAlchemy | Yes | No | None — industry standard |
| Database | SQLite (WAL) | Yes | Yes (PostgreSQL, Cosmos) | Write contention with Gunicorn workers |
| Authentication | Flask-JWT-Extended | Yes | Yes (sessions, API keys, OAuth2) | None |
| PDF parsing | PyMuPDF or pdfplumber | Partial | Partial (listed as options, not decided) | **TBD** — should decide |
| LLM extraction | Anthropic Claude | Yes | Yes (regex, Textract, GPT) | None |
| Request validation | Marshmallow or Pydantic | Partial | Partial (listed as options, not decided) | **TBD** — should decide |
| UI component library | TBD | No | No | **TBD** — acceptable to defer |
| Observability | App Insights | Yes | No explicit alternatives | `opencensus-ext-azure` vs `azure-monitor-opentelemetry` not decided |
| Security headers | Flask-Talisman or manual | Partial | No | **TBD** — should decide |
| Frontend build | Vite | Yes (implied) | No | None |
| CI/CD | GitHub Actions | Yes | No explicit alternatives | None |

### Gaps and Recommendations

| ID | Gap | Priority | Recommendation |
|----|-----|----------|----------------|
| TECH-1 | Three technology choices remain undecided: PDF parser, request validation, and App Insights SDK. While the UI component library can reasonably be deferred (it doesn't affect backend architecture), the PDF parser and validation library affect error handling architecture and the App Insights SDK choice determines the observability integration pattern. | Should Address | Commit to specific choices: (a) **pdfplumber** for PDF parsing — better table extraction for DME forms with tabular data. (b) **Marshmallow** for validation — native Flask integration via Flask-Smorest or Flask-Marshmallow, schema-first approach aligns with the separation of concerns principle. (c) **azure-monitor-opentelemetry** — opencensus is deprecated in favor of OpenTelemetry. |
| TECH-2 | The requirements (NFR-6.5) specify OpenAPI/Swagger documentation at `/api/v1/docs`. The technology choices table doesn't include a Swagger/OpenAPI tool. Flask doesn't generate API docs automatically — a library is needed (e.g., Flask-Smorest, Flasgger, flask-apispec). | Should Address | Add an OpenAPI documentation library to the technology choices. Flask-Smorest is recommended — it integrates with Marshmallow schemas (if chosen per TECH-1) and auto-generates OpenAPI 3.0 docs with Swagger UI. |
| TECH-3 | Flask-Talisman vs "manual middleware" for security headers is undecided. This affects whether CSP (Content Security Policy) is configured, which is important when serving a React SPA that loads JavaScript bundles. | Consider | Commit to Flask-Talisman. It handles HSTS, CSP, and other security headers with sensible defaults. Note that the CSP policy will need to allow the React bundle's script sources (e.g., `'self'` and possibly inline styles from the UI component library). |

### Verdict: **Partially Addressed**

---

## 6. Deployment & Operational Readiness

### Current State

The deployment model is detailed with Azure App Service configuration tables, a CI/CD pipeline diagram with 8 stages, and a local development setup. Infrastructure requirements are sized. The design covers production, CI/CD, and local development environments.

### Strengths

- Azure App Service configuration table is specific and actionable (startup command, paths, plan)
- CI/CD pipeline includes a smoke test step
- Local development setup is practical with Vite proxy for API requests
- Infrastructure requirements table provides clear sizing guidance

### Gaps and Recommendations

| ID | Gap | Priority | Recommendation |
|----|-----|----------|----------------|
| OPS-1 | No database backup strategy. SQLite on the Azure filesystem can corrupt (disk issues, interrupted writes, deployment errors). There is no mention of backup, snapshot, or recovery procedures. For an assessment this is low risk, but the design should acknowledge the risk. | Should Address | Add a brief note: "For assessment purposes, SQLite has no backup mechanism. For production, either (a) periodic file copy/backup of the `.db` file, or (b) migrate to a managed database with built-in backups." This demonstrates awareness to reviewers. |
| OPS-2 | The CI/CD pipeline doesn't specify what happens on first deployment when the database doesn't exist. Does the app auto-create the SQLite file? Does the pipeline run `flask db upgrade`? What about subsequent deploys with schema changes? | Should Address | Specify that the deployment pipeline SHOULD run `flask db upgrade` after deploying code (or that the application auto-runs migrations on startup). For SQLite, the first `flask db upgrade` creates the database file. |
| OPS-3 | No rollback strategy if a deployment or smoke test fails. Stage 8 runs a health check, but if it fails, does the pipeline roll back to the previous version? Azure App Service supports deployment slots for blue/green, but the design doesn't mention this. | Consider | Add a brief note: "If the smoke test fails, the deployment SHOULD be rolled back using Azure App Service's built-in deployment rollback. Deployment slots are deferred for v1." |
| OPS-4 | No mention of how application logs (Python logging output) reach Azure Application Insights. The design mentions the App Insights SDK but doesn't specify whether Flask's built-in logger is configured to send to App Insights, or whether only the SDK's auto-instrumentation is used. | Consider | Specify that the App Insights SDK auto-captures request traces, dependency calls, and exceptions. Python `logging` module output SHOULD also be routed to App Insights via the SDK's logging handler, so that custom log statements (e.g., LLM interaction logs per FR-3.3.5) appear in App Insights. |

### Verdict: **Partially Addressed**

---

## 7. Requirements Coverage

### Coverage Matrix

| Requirement | Addressed In Design? | Section | Notes |
|-------------|---------------------|---------|-------|
| FR-3.1.1 (User Registration) | Yes | 5.1, 7.1 | Password hashing, validation covered |
| FR-3.1.2 (User Login) | Yes | 5.1, 7.1 | JWT generation, error handling |
| FR-3.1.3 (Token Refresh) | Partial | 7.1, 11 | Mentioned but no data flow; storage strategy is open question |
| FR-3.1.4 (Protected Routes) | Yes | 7.1 | Auth flow diagram covers this |
| FR-3.2.1 (Create Order) | Yes | 5.2, 4.1 | |
| FR-3.2.2 (List Orders) | Yes | 3.1, 4.2 | Pagination/filtering covered in requirements, architecture supports it |
| FR-3.2.3 (Get Order by ID) | Yes | 4.2 | Document inclusion addressed by data model |
| FR-3.2.4 (Update Order) | Yes | 4.2, 5.2 | |
| FR-3.2.5 (Delete Order) | Partial | 4.2 | Cascade delete mentioned in requirements but no data flow for file cleanup |
| FR-3.3.1 (Document Upload) | Yes | 5.3, 7.4 | File validation, size limits, storage |
| FR-3.3.2 (PDF Text Extraction) | Yes | 3.4, 5.3 | Multi-page handling noted |
| FR-3.3.3 (LLM Structured Extraction) | Yes | 3.4, 5.3 | Structured prompt, schema validation |
| FR-3.3.4 (Auto-Population) | Partial | 5.3 | **Missing `error_message` field on Order** (see DATA-1) |
| FR-3.3.5 (LLM Error Handling) | Yes | 3.4, 5.4 | Retry, timeout, sanitized errors all covered |
| FR-3.4.1 (Request Logging) | Yes | 5.5 | Middleware approach, non-blocking |
| FR-3.4.2 (Log Retrieval) | Partial | 4 (API table) | Endpoint listed but no data flow or access control model |
| FR-3.5.1 (Auth Pages) | Yes | 3.2 | |
| FR-3.5.2 (Order Dashboard) | Yes | 3.2 | |
| FR-3.5.3 (UI/UX) | Partial | 3.2, 9 | Component library TBD (acceptable) |
| NFR-6.1 (Security) | Yes | 7 | Comprehensive threat/mitigation table |
| NFR-6.2 (Performance) | Partial | 3.3, 3.4 | Indexes not in data model (See DATA-4) |
| NFR-6.3 (Reliability) | Yes | 3.3, 3.4, 5.4 | LLM outage handling, WAL mode |
| NFR-6.4 (Code Quality) | N/A | — | Implementation-level, not applicable to HLD |
| NFR-6.5 (Documentation) | Partial | 9 | **No OpenAPI/Swagger tool chosen** (See TECH-2) |
| NFR-6.6 (Deployment) | Yes | 8 | Azure, GitHub Actions, startup command |

### Gaps

| ID | Requirement | Status | Recommendation |
|----|-------------|--------|----------------|
| COV-1 | FR-3.3.4 (error description stored on failure) | Missing field | Add `error_message` field to Order entity (see DATA-1) |
| COV-2 | NFR-6.5 (OpenAPI/Swagger docs at `/api/v1/docs`) | Missing technology | Choose an OpenAPI library (see TECH-2) |
| COV-3 | FR-3.1.3 (Token Refresh) | Partially covered | Document the refresh flow and decide on storage strategy (see FLOW-1, SEC-2) |

### Verdict: **Sufficient**

---

## 8. Specification Clarity

### Items Requiring Clarification

| ID | Item | Section | Issue | Question |
|----|------|---------|-------|----------|
| UNCLEAR-1 | "Extraction status polling" | 3.2 (Frontend table) | **Contradictory** | Section 3.2 says the Document Upload subcomponent handles "extraction status polling," but Section 6.3 explicitly chooses synchronous extraction. If extraction is synchronous, there is nothing to poll — the HTTP response contains the result. Which is correct? |
| UNCLEAR-2 | Health check endpoint path | 6.7 vs 4.4 (requirements) | **Contradictory** | Section 6.7 URL routing strategy lists `/health` as a direct route, but the requirements (Section 4.4) specify `GET /api/v1/health`. The CI/CD smoke test in Section 8.2 references `/api/v1/health`. Which path should it be? |
| UNCLEAR-3 | Gunicorn worker count | 8.1 | **Ambiguous** | Configuration table says "2-4 workers" but Open Question #5 suggests 2 as the starting point. With SQLite's single-writer constraint, more workers increase write contention. The design SHOULD specify a concrete default (2) rather than a range. |
| UNCLEAR-4 | Activity log admin access | 3.1, 7.1 | **Undefined** | The activity log endpoint is called an "admin endpoint" (requirements Section 4.3) but the authorization model is flat (all users equal). Can any authenticated user access activity logs? This needs a clear answer — it affects both the backend auth logic and the frontend navigation. |

### Verdict: **Partially Addressed**

---

## Summary of Recommendations

### Must Address (Blocking — resolve before low-level design)

1. **DATA-1:** Add `error_message` (text, nullable) field to Order entity — required by FR-3.3.4 to store extraction failure descriptions.
2. **FLOW-3:** Resolve the contradiction between synchronous extraction (Section 6.3) and "extraction status polling" (Section 3.2). Pick one model and update the design consistently.

### Should Address (High Priority)

1. **SEC-2:** Decide refresh token storage strategy (database-backed vs. signed JWT). This determines whether token revocation/logout works and is currently an unresolved open question.
2. **SEC-3:** Add rate limiting to the LLM extraction endpoint to prevent cost abuse and resource exhaustion.
3. **TECH-1:** Commit to specific choices for PDF parser, validation library, and App Insights SDK. Three undecided technologies create ambiguity for the low-level design.
4. **TECH-2:** Choose an OpenAPI/Swagger documentation library (Flask-Smorest recommended) to satisfy NFR-6.5.
5. **FLOW-1:** Document the token refresh data flow — it has unique auth requirements and is critical for the frontend's session management.
6. **FLOW-2:** Document the order deletion cascade flow including physical PDF file cleanup.
7. **DATA-2:** Clarify the `role` field: specify a default value or remove it from v1.
8. **DATA-3:** Clarify the relationship between Document.extracted_data (JSON) and Order's individual extracted fields — which is source of truth.
9. **ARCH-3:** Define route precedence for API 404s vs. SPA catch-all to prevent implementation ambiguity.
10. **OPS-1:** Acknowledge SQLite backup risk and mitigation.
11. **OPS-2:** Specify database migration strategy in CI/CD pipeline.

### Consider (Medium Priority)

1. **ARCH-1:** Add Gunicorn to the architecture diagram as an explicit component.
2. **ARCH-2:** Clarify that activity logging captures all requests (including auth failures).
3. **DATA-4:** Note required database indexes in the data model section.
4. **SEC-1:** Acknowledge HS256 implications and document when to upgrade to RS256.
5. **SEC-4:** Note PDF parser crash protection as a security mitigation.
6. **TECH-3:** Commit to Flask-Talisman for security headers.
7. **OPS-3:** Describe rollback strategy for failed deployments.
8. **OPS-4:** Specify how Python logging integrates with Application Insights.
9. **FLOW-4:** Clarify admin activity log endpoint access control.
10. **UNCLEAR-2:** Resolve health check endpoint path inconsistency.
11. **UNCLEAR-3:** Commit to 2 Gunicorn workers as default.
12. **UNCLEAR-4:** Define who can access activity logs given the flat auth model.

---

## Findings Summary

| Area | Verdict | Must | Should | Consider |
|------|---------|------|--------|----------|
| Architecture & Components | Sufficient | 0 | 1 | 2 |
| Data Model | Partially Addressed | 1 | 2 | 1 |
| Data Flows | Partially Addressed | 1 | 2 | 1 |
| Security | Sufficient | 0 | 2 | 2 |
| Technology Choices | Partially Addressed | 0 | 2 | 1 |
| Deployment & Ops | Partially Addressed | 0 | 2 | 2 |
| Requirements Coverage | Sufficient | 0 | 0 | 0 |
| Specification Clarity | Partially Addressed | 0 | 0 | 4 |
| **Total** | | **2** | **11** | **13** |
