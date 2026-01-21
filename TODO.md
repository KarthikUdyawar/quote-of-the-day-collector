Below is a **clean, actionable `TODO.md`** generated **strictly from your existing documentation set**
(`README.md`, `ARCHITECTURE.md`, `PRD.md`, `DESIGN.md`, `TECH_RULES.md`, `CHANGELOG.md`).

This is **not a wish list** — it reflects:

* What is **implemented**
* What is **missing but implied**
* What is **required to harden v0.1.0**
* What is **clearly next**, without scope creep

---

# ✅ TODO

## Project

**Quote of the Day Collector**

## Baseline Version

**v0.1.0**

## Purpose

This file tracks **engineering and operational tasks** required to:

* Stabilize the current release
* Improve reliability and maintainability
* Prepare for future evolution **without violating tech rules**

---

## 🟢 Completed (v0.1.0)

* [x] RSS-based quote fetching
* [x] GUID-based deduplication
* [x] Fetch history audit logging
* [x] SQLite as authoritative state store
* [x] Quote classification using local Ollama
* [x] One-classification-per-quote guarantee
* [x] Branded image generation with Pillow
* [x] Category-based theming
* [x] Structured image storage
* [x] Telegram upload with MarkdownV2 captions
* [x] Exactly-once upload tracking
* [x] CLI-based execution for all services
* [x] Service-specific logging
* [x] Docker Compose deployment
* [x] Architecture, PRD, Design, Tech Rules documentation

---

## 🟡 Required Hardening (Still v0.1.0)

### Configuration & Safety

* [ ] Validate required environment variables at startup
* [ ] Fail fast on missing `TELEGRAM_BOT_TOKEN`
* [ ] Fail fast on missing `TELEGRAM_CHAT_ID`
* [ ] Centralize config loading logic

### Database Integrity

* [ ] Add explicit UNIQUE constraint on `quotes.guid`
* [ ] Enforce one-row-per-quote constraint in:

  * [ ] `quote_classifications`
  * [ ] `quote_images`
  * [ ] `telegram_uploads`
* [ ] Add foreign key constraints where applicable
* [ ] Enable SQLite foreign key enforcement on connection

---

## 🟡 Observability & Operations

### Logging

* [ ] Standardize log format across services
* [ ] Include run-id / execution timestamp in logs
* [ ] Log summary metrics at end of each run

### Metrics & Visibility

* [ ] Add CLI command to show full pipeline state
* [ ] Add per-stage counts (fetched / classified / imaged / uploaded)
* [ ] Add last-success timestamps per service

---

## 🟡 Failure Handling Improvements

* [ ] Add retry backoff for Telegram upload failures
* [ ] Handle partial RSS feed failures gracefully
* [ ] Log LLM timeouts explicitly
* [ ] Add image generation exception categorization

---

## 🟠 Developer Experience

### Code Quality

* [ ] Add docstrings to all public functions
* [ ] Standardize function naming across services
* [ ] Remove duplicated utility logic (if any)

### Tooling

* [ ] Add `makefile` or task runner aliases
* [ ] Add `--dry-run` mode to services
* [ ] Add `--limit` / `--since` flags where applicable

---

## 🔵 Documentation Tasks

* [ ] Add **OPERATIONS.md** (how to run daily in production)
* [ ] Add **TROUBLESHOOTING.md**
* [ ] Document Ollama model assumptions
* [ ] Add example `.env.example`

---

## 🔵 Testing (Deferred but Planned)

> Testing is intentionally minimal in v0.1.0
> These tasks prepare for future stability without violating tech rules.

* [ ] Add basic smoke tests for each service
* [ ] Add database integrity verification script
* [ ] Add end-to-end pipeline dry run test
* [ ] Add image generation snapshot test

---

## 🔴 Explicitly Out of Scope (Do NOT Do)

* [ ] ❌ Do not add Redis
* [ ] ❌ Do not add Celery or task queues
* [ ] ❌ Do not add ORMs
* [ ] ❌ Do not add cloud-managed services
* [ ] ❌ Do not add UI/dashboard yet

---

## 🔮 Future (Post v0.1.x – Non-Blocking)

> These require new PRD & Tech Rules updates.

* [ ] PostgreSQL migration design
* [ ] Multiple publishing targets
* [ ] Reclassification support
* [ ] Advanced analytics
* [ ] Content scheduling policies

---

## 📌 Working Principle

> **If it’s not in the database, it’s not done.**
> **If it violates TECH_RULES.md, it doesn’t get merged.**

---

## 📄 File Name

```
TODO.md
```

---

If you want next, I can generate:

* 🛠️ **OPERATIONS.md**
* 🚨 **RUNBOOK.md**
* 🧪 **TEST_PLAN.md**
* 🧾 **ADR-0001: Why SQLite**

Just say 👍
