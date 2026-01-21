# 🧱 Tech Rules (Tech Stack Definition)

## Product

**Quote of the Day Collector**

## Version

**v0.1.0**

## Status

**Authoritative – Enforced**

---

## 1. Purpose of This Document

This document defines the **approved technology stack**, **usage rules**, and **constraints** for the project.

Its goals are to:

* Prevent tech sprawl
* Maintain architectural consistency
* Make onboarding contributors easy
* Preserve the system’s core principles (state-driven, deterministic, idempotent)

---

## 2. Core Philosophy

> **Simplicity beats sophistication.
> State beats orchestration.
> Determinism beats automation magic.**

All tech choices must support:

* Explicit state
* Restart safety
* Inspectability
* Minimal dependencies

---

## 3. Approved Programming Language

### 3.1 Python

**Version**

* ✅ **Python 3.12 only**

**Rules**

* No backward compatibility required
* Use standard library wherever possible
* Prefer clarity over clever abstractions

**Disallowed**

* Mixing multiple Python versions
* Dynamic runtime version switching

---

## 4. Runtime & Execution Model

### 4.1 Execution Style

* CLI-driven scripts
* One process = one responsibility
* No long-running daemon assumptions (except schedulers)

### 4.2 Scheduling

* `schedule` library allowed
* Cron allowed externally (Docker / host)
* No internal async job queues

---

## 5. Data Storage Rules

### 5.1 Primary Database

**Approved**

* ✅ **SQLite**

**Rules**

* SQLite is the **single source of truth**
* Database state defines workflow progress
* No hidden state (cache ≠ state)

**Disallowed**

* In-memory-only state
* Redis, MongoDB, or key-value stores
* Multiple databases per environment

---

### 5.2 Schema Management

* Schema defined explicitly
* No auto-migration frameworks
* Schema changes must update:

  * `ARCHITECTURE.md`
  * `CHANGELOG.md`

---

## 6. Service Communication Rules

### 6.1 Inter-Service Communication

* ❌ No direct service-to-service calls
* ❌ No message queues
* ✅ Database-mediated coordination only

---

## 7. Machine Learning / AI Stack

### 7.1 LLM Runtime

**Approved**

* ✅ **Ollama (local LLM execution)**

**Rules**

* Local inference only
* Deterministic prompts
* Classification is append-only (no reclassification)

**Disallowed**

* Cloud LLM APIs
* Hidden prompt mutation
* Auto-retry hallucination loops

---

## 8. Image Generation Stack

### 8.1 Image Library

**Approved**

* ✅ **Pillow**

**Rules**

* Deterministic rendering per quote
* Fonts and colors must be explicit
* No runtime randomness in layout

**Disallowed**

* Headless browsers
* GPU-based rendering frameworks

---

## 9. Messaging / Publishing Stack

### 9.1 Telegram Integration

**Approved**

* ✅ **python-telegram-bot**

**Rules**

* MarkdownV2 formatting enforced
* Message IDs must be persisted
* Exactly-once upload semantics

**Disallowed**

* Webhooks (polling / direct calls only)
* Multiple bot tokens per environment

---

## 10. Dependency Management

### 10.1 Python Dependencies

**Approved**

* `pyproject.toml` as the source of truth
* Minimal, explicit dependencies

**Rules**

* Every dependency must be justified
* No transitive dependency reliance
* Lock files must be committed

---

## 11. Configuration Management

### 11.1 Environment Variables

**Approved**

* `.env` files
* OS environment variables

**Rules**

* Secrets never hardcoded
* No config files containing secrets
* Fail fast if required variables are missing

---

## 12. Containerization Rules

### 12.1 Docker

**Approved**

* Docker
* Docker Compose

**Rules**

* One service per container
* No “mega containers”
* Shared SQLite via volume only

**Disallowed**

* Kubernetes (for current scope)
* Sidecar containers

---

## 13. Logging Rules

### 13.1 Logging Strategy

**Approved**

* Python `logging` module

**Rules**

* File + STDOUT logging
* One log file per service
* No silent failures

**Disallowed**

* External log aggregation tools
* Logging-as-a-service dependencies

---

## 14. Error Handling Rules

* Fail locally, not globally
* Log errors, don’t swallow them
* Leave state untouched on failure
* Retrying must always be safe

---

## 15. Testing Rules (Current Scope)

**Allowed**

* Manual testing via CLI
* Ad-hoc validation scripts

**Deferred**

* Unit test frameworks
* Integration test harnesses

(Testing strategy to be defined in a future document.)

---

## 16. Forbidden Technologies (Explicit)

The following are **explicitly disallowed** in v0.1.0:

* Redis
* Kafka / RabbitMQ
* Celery
* Kubernetes
* ORM frameworks
* Auto-magic workflow engines
* Cloud-managed databases
* SaaS observability tools

---

## 17. Change Control

Any change to the tech stack requires:

1. Update to this document
2. Update to `ARCHITECTURE.md`
3. Entry in `CHANGELOG.md`

No exceptions.

---

## 18. File Name Recommendation

```
TECH_RULES.md
```

### Final Documentation Set (Authoritative)

```
README.md
ARCHITECTURE.md
PRD.md
DESIGN.md
TECH_RULES.md
CHANGELOG.md
```

---

## 19. Final Statement

This project is **intentionally conservative** in tech choices.

> *The best system is the one you can reason about at 3 AM.*
