# 🧩 Design Document

## Product

**Quote of the Day Collector**

## Version

**v0.1.0**

## Status

**Stable – Implemented**

---

## 1. Purpose of This Document

This document describes the **technical design** of the Quote of the Day Collector system, including:

* Component responsibilities
* Data flow and state transitions
* Design decisions and trade-offs
* Failure handling and idempotency guarantees

It serves as a reference for:

* Future contributors
* Refactoring or scaling efforts
* Production hardening

---

## 2. Design Principles

### 2.1 State-Driven Architecture

* The **SQLite database is the single source of truth**
* No in-memory or external state assumptions
* Progress is inferred from table existence, not flags

> *If it’s in the table, it’s done.*

---

### 2.2 Idempotency by Design

Every service can be:

* Re-run safely
* Crashed and restarted
* Executed independently

This is achieved via:

* Unique constraints (GUIDs)
* Append-only logs
* One-row-per-stage guarantees

---

### 2.3 Loose Coupling

* Each service is a standalone Python process
* No direct service-to-service calls
* Coordination happens **only through the database**

---

## 3. High-Level Component Design

```
+--------------+
| RSS Sources  |
+------+-------+
       |
       v
+------+-------+
| Quote Fetcher|
+------+-------+
       |
       v
+------+-------+
|   SQLite DB  |
+--+---+---+---+
   |   |   |
   v   v   v
Classifier Generator Uploader
```

---

## 4. Component-Level Design

### 4.1 Quote Fetcher (`quote_fetcher.py`)

#### Responsibilities

* Fetch RSS feeds
* Parse quote entries
* Deduplicate via `guid`
* Log every fetch run

#### Design Decisions

* **No updates** to existing quotes → immutability
* Fetch history is append-only for auditability
* Feed metadata stored separately from quotes

#### Failure Behavior

* Feed failure → logged in `fetch_history`
* Partial success allowed

---

### 4.2 Quote Classifier (`quote_classifier.py`)

#### Responsibilities

* Select quotes without classification
* Classify using local Ollama LLM
* Persist classification metadata

#### Design Decisions

* Exactly one classification per quote
* No reclassification logic (by design)
* Reasoning stored for audit/debugging

#### Failure Behavior

* LLM failure leaves quote unclassified
* Safe to retry later

---

### 4.3 Image Generator (`quote_image_generator.py`)

#### Responsibilities

* Render square quote images
* Apply category-based themes
* Dynamically size and wrap text
* Persist image metadata

#### Filesystem Design

```
images/
└── <category>/
    └── <DD-MM-YYYY>/
        └── quote_<id>_<author>.png
```

#### Design Decisions

* One image per quote
* Filesystem + DB tracking for verification
* Image generation is deterministic per quote

---

### 4.4 Telegram Uploader (`telegram_uploader.py`)

#### Responsibilities

* Upload images to Telegram
* Escape captions for MarkdownV2
* Track message IDs
* Support batch and async uploads

#### Design Decisions

* Uploads tracked for exactly-once delivery
* Async support for rate limiting
* CLI-driven actions (`upload`, `stats`, `test`)

#### Failure Behavior

* Failed uploads are retried safely
* No duplicate uploads due to DB tracking

---

## 5. Data Design

### 5.1 Database Choice: SQLite

#### Rationale

* Simple deployment
* Strong consistency
* File-based portability
* Sufficient for current workload

#### Trade-offs

* Limited concurrency
* Not horizontally scalable (by design)

---

### 5.2 Table Responsibility Mapping

| Table                   | Purpose                |
| ----------------------- | ---------------------- |
| `feed_info`             | Feed metadata          |
| `fetch_history`         | Fetch audit log        |
| `quotes`                | Canonical quote store  |
| `quote_classifications` | Classification state   |
| `quote_images`          | Image generation state |
| `telegram_uploads`      | Publishing state       |

---

## 6. Processing & State Transitions

### 6.1 Implicit State Model

| State           | Evidence                              |
| --------------- | ------------------------------------- |
| Fetched         | Row exists in `quotes`                |
| Classified      | Row exists in `quote_classifications` |
| Image Generated | Row exists in `quote_images`          |
| Uploaded        | Row exists in `telegram_uploads`      |

No explicit status flags are used.

---

## 7. Failure Handling Strategy

| Stage            | Failure Handling  |
| ---------------- | ----------------- |
| Fetching         | Log and continue  |
| Classification   | Skip, retry later |
| Image generation | Skip, retry later |
| Telegram upload  | Retry safely      |

Failures never corrupt global state.

---

## 8. Logging & Observability

### Logging Strategy

* One log file per service
* Logs written to:

  * File (`logs/*.log`)
  * STDOUT (Docker-friendly)

### Observability Goals

* Diagnose failures per stage
* Audit historical runs
* Trace quote lifecycle via DB

---

## 9. Deployment Design

### 9.1 Docker Compose

* One container per service
* Shared SQLite volume
* Optional Ollama container

### 9.2 Local Execution

* Services runnable independently
* Virtual environment supported

---

## 10. Security Considerations

* No user authentication
* Secrets managed via environment variables
* No external write access except Telegram API

---

## 11. Scalability Considerations (Future)

Not implemented, but enabled by design:

* Migration to PostgreSQL
* Horizontal service scaling
* Multiple publishing targets

---

## 12. Design Constraints

* SQLite as authoritative store
* Exactly-once semantics
* Deterministic processing
* Minimal dependencies

---

## 13. Known Limitations

* No UI/dashboard
* No reclassification logic
* No quote editing
* Single publishing platform

---

## 14. Design Summary

**This design prioritizes correctness over cleverness.**

* Simple data model
* Explicit state transitions
* Restart-safe execution
* Clear auditability

> *The database is the workflow.*
