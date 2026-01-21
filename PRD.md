# 📄 Product Requirements Document (PRD)

## Product Name

**Quote of the Day Collector**

## Version

**v0.1.0**

## Document Status

**Baseline PRD (Aligned with Initial Stable Release)**

---

## 1. Product Overview

### 1.1 Description

**Quote of the Day Collector** is a fully automated, deterministic content pipeline that fetches quotes from RSS feeds, classifies them into categories, generates branded quote images, and publishes them to a Telegram channel. The entire system is state-driven, idempotent, restart-safe, and backed by SQLite.

### 1.2 Product Vision

To provide a **hands-free, reliable quote publishing system** that guarantees:

* No duplicate content
* Exactly-once processing at each pipeline stage
* Clear auditability via database state

---

## 2. Problem Statement

Manual quote curation and publishing is:

* Time-consuming
* Error-prone (duplicates, missed posts)
* Difficult to scale consistently

Existing automation tools often lack:

* Deterministic state tracking
* Strong idempotency guarantees
* Transparent, inspectable pipelines

---

## 3. Goals & Objectives

### 3.1 Primary Goals

* Automate end-to-end quote ingestion → publishing
* Ensure idempotent, restart-safe processing
* Maintain full traceability via database state

### 3.2 Success Metrics

* Zero duplicate Telegram uploads
* Zero duplicate quotes (GUID-based)
* Successful pipeline re-runs without manual cleanup
* Accurate per-stage statistics (fetch, classify, generate, upload)

---

## 4. Target Users & Personas

### 4.1 Primary Users

* **Content Curators** running Telegram quote channels
* **Developers** building automated content pipelines
* **Solo creators** managing daily motivational/educational content

### 4.2 User Needs

* Minimal manual intervention
* Reliable automation
* Ability to inspect and debug state via logs and database

---

## 5. In-Scope Features (Functional Requirements)

### 5.1 Quote Fetching

* Fetch quotes from RSS feeds
* Parse and store feed metadata
* Prevent duplicate quotes using GUID
* Log every fetch attempt (success or failure)

**Acceptance Criteria**

* Duplicate GUIDs are skipped
* Every fetch run is logged in `fetch_history`

---

### 5.2 Quote Classification

* Select unclassified quotes from the database
* Classify quotes using a local LLM (Ollama)
* Store category, confidence, and reasoning

**Acceptance Criteria**

* Exactly one classification per quote
* Re-running classifier skips already-classified quotes

---

### 5.3 Image Generation

* Generate square, social-media-ready images
* Apply category-based visual theming
* Support dynamic font sizing and text wrapping
* Save images in structured folders

**Acceptance Criteria**

* One image per quote
* Image path tracked in `quote_images`
* Re-runs do not regenerate existing images

---

### 5.4 Telegram Publishing

* Upload generated images to Telegram
* Format captions using MarkdownV2
* Support batch uploads and async handling
* Track uploads with message IDs

**Acceptance Criteria**

* Each quote image uploaded exactly once
* Uploads tracked in `telegram_uploads`
* Failed uploads are retry-safe

---

### 5.5 Statistics & Observability

* Track totals and pending work per stage
* Provide CLI commands for stats
* Write logs per service

**Acceptance Criteria**

* Stats reflect database truth
* Logs written to file and stdout

---

## 6. Non-Functional Requirements

### 6.1 Reliability

* System must be restart-safe
* Partial failures must not corrupt state

### 6.2 Idempotency

* Every pipeline stage must be safely re-runnable
* State inferred only from database tables

### 6.3 Performance

* Designed for batch processing
* Async upload support for Telegram rate limits

### 6.4 Maintainability

* Loosely coupled services
* Clear separation of responsibilities

---

## 7. System Architecture (Summary)

### 7.1 Architecture Style

* Loosely coupled, pipeline-based micro-services
* SQLite as the single source of truth

### 7.2 Pipeline Flow

```
RSS Feeds
 → Quote Fetcher
 → Quote Classifier
 → Image Generator
 → Telegram Uploader
```

### 7.3 State Management Principle

> **State is truth. Tables define progress.**

No explicit status flags — progress is inferred from table presence.

---

## 8. Data Model (Authoritative)

### Core Tables

* `feed_info`
* `fetch_history`
* `quotes`
* `quote_classifications`
* `quote_images`
* `telegram_uploads`

### Integrity Rules

* GUID must be unique per quote
* One classification per quote
* One image per quote
* Exactly-once Telegram upload

---

## 9. Deployment & Operations

### 9.1 Deployment Model

* Docker Compose (recommended)
* Each service independently runnable
* SQLite shared via Docker volume
* Ollama runs locally (GPU optional)

### 9.2 Configuration

* Environment variables for Telegram credentials
* `.env` file supported

---

## 10. Risks & Mitigations

| Risk                   | Mitigation                    |
| ---------------------- | ----------------------------- |
| RSS feed downtime      | Logged, retry-safe fetch runs |
| LLM failure            | Quote remains unclassified    |
| Image generation error | Safe retry                    |
| Telegram API limits    | Async uploads + delays        |
| System crash           | Database-driven recovery      |

---

## 11. Out of Scope (Current Version)

* Web UI or dashboard
* User authentication
* Multi-platform publishing (beyond Telegram)
* External database (PostgreSQL, etc.)
* Cloud-managed deployment

---

## 12. Roadmap (Derived from Current State)

### Current Release

* **v0.1.0** – Initial stable, end-to-end pipeline

### Future Considerations (Not Implemented)

* Additional quote sources
* More publishing targets
* Advanced analytics dashboards
* Database migration to PostgreSQL

---

## 13. Open Questions

* How many RSS feeds are expected at scale?
* Long-term storage strategy for images?
* Should historical quotes ever be reprocessed?

---

## 14. Approval & Alignment

**PRD Alignment**

* ✅ README.md
* ✅ ARCHITECTURE.md
* ✅ CHANGELOG.md

**Status:**
✔ Feature-complete for v0.1.0
✔ Architecture-consistent
✔ Production-safe for controlled workloads

