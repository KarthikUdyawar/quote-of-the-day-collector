You’re absolutely right — thanks for pasting the **actual DDL**.
Below is a **fully corrected, field-accurate `ARCHITECTURE.md`**, rewritten **strictly from your real schema**.
No invented columns, no imaginary FKs.

You can **drop this in as `ARCHITECTURE.md` verbatim**.

---

# 🏗️ ARCHITECTURE

**Quote of the Day Collector — v0.1.0**

---

## 1. System Purpose

**Quote of the Day Collector** is a deterministic content pipeline that:

1. Fetches quotes from RSS feeds
2. Deduplicates using GUIDs
3. Classifies quotes using a local LLM (Ollama)
4. Generates branded quote images
5. Publishes images to Telegram
6. Tracks state entirely via SQLite

The system is **state-driven**, **idempotent**, and **restart-safe**.

---

## 2. High-Level Architecture

```mermaid
flowchart LR
    A[RSS Feeds] --> B[Quote Fetcher]
    B --> C[(SQLite DB)]

    C --> D[Quote Classifier]
    D --> C

    C --> E[Image Generator]
    E --> F[Image Files]
    E --> C

    C --> G[Telegram Uploader]
    G --> H[Telegram Channel]
```

---

## 3. Core Services

### 3.1 Quote Fetcher

**Responsibilities**

* Fetch RSS feeds
* Parse quote entries
* Deduplicate using `guid`
* Persist fetch metrics

**Writes**

* `feed_info`
* `fetch_history`
* `quotes`

**Design Notes**

* No updates to existing quotes
* Fetch results always recorded (success or failure)
* Safe to run continuously

---

### 3.2 Quote Classifier

**Responsibilities**

* Select unclassified quotes
* Classify using Ollama
* Store classification metadata

**Writes**

* `quote_classifications`

**Guarantees**

* Exactly one classification per quote
* Re-runs skip already-classified quotes

---

### 3.3 Image Generator

**Responsibilities**

* Generate square social-media-ready images
* Organize images by category and date
* Track generation state

**Writes**

* Filesystem (`images/`)
* `quote_images`

---

### 3.4 Telegram Uploader

**Responsibilities**

* Upload generated images
* Format captions (MarkdownV2 safe)
* Track upload status

**Writes**

* `telegram_uploads`

---

## 4. Processing Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Fetched
    Fetched --> Classified
    Classified --> ImageGenerated
    ImageGenerated --> Uploaded
    Uploaded --> [*]
```

State is inferred from table presence — **no status flags required**.

---

## 5. Sequence Diagrams

### 5.1 Feed Fetching

```mermaid
sequenceDiagram
    autonumber
    participant RSS
    participant Fetcher
    participant DB

    Fetcher->>RSS: Fetch feed
    RSS-->>Fetcher: Feed items
    Fetcher->>DB: Upsert feed_info
    Fetcher->>DB: Insert quotes (dedupe by guid)
    Fetcher->>DB: Insert fetch_history
```

---

### 5.2 Quote Classification

```mermaid
sequenceDiagram
    autonumber
    participant Classifier
    participant Ollama
    participant DB

    Classifier->>DB: Select quotes without classification
    loop Each quote
        Classifier->>Ollama: Classify quote
        Ollama-->>Classifier: category, confidence, reasoning
        Classifier->>DB: Insert quote_classifications
    end
```

---

### 5.3 Image Generation

```mermaid
sequenceDiagram
    autonumber
    participant Generator
    participant DB
    participant FS

    Generator->>DB: Select classified quotes without images
    loop Each quote
        Generator->>FS: Render & save PNG
        Generator->>DB: Insert quote_images
    end
```

---

### 5.4 Telegram Upload

```mermaid
sequenceDiagram
    autonumber
    participant Uploader
    participant DB
    participant Telegram

    Uploader->>DB: Select images not uploaded
    loop Each image
        Uploader->>Telegram: sendPhoto
        Telegram-->>Uploader: message_id
        Uploader->>DB: Insert telegram_uploads
    end
```

Got it 👍 — you’re right, that **end-to-end pipeline sequence diagram** was missing.
Below is the **corrected addition** you should include in **`ARCHITECTURE.md`**.
This diagram is **important** because it shows the *entire system as one flow*, not isolated services.

---

### 5.5 Full Pipeline Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Source
    participant Fetcher
    participant DB
    participant Classifier
    participant Generator
    participant Telegram

    Source->>Fetcher: Fetch quotes (RSS)
    Fetcher->>DB: Insert quotes (dedupe by guid)
    Fetcher->>DB: Insert feed_info / fetch_history

    Classifier->>DB: Read unclassified quotes
    Classifier->>Classifier: Ollama classification
    Classifier->>DB: Save quote_classifications

    Generator->>DB: Fetch classified quotes without images
    Generator->>Generator: Generate image
    Generator->>DB: Save quote_images

    Telegram->>DB: Fetch pending images
    Telegram->>Telegram: Upload image
    Telegram->>DB: Save telegram_uploads
```

---

## 6. Database Schema (Authoritative)

### 6.1 Entity Relationship Diagram

```mermaid
erDiagram
    feed_info ||--o{ fetch_history : logs
    quotes ||--o{ quote_classifications : classified
    quotes ||--o{ quote_images : rendered
    quotes ||--o{ telegram_uploads : published

    feed_info {
        INTEGER id PK
        TEXT title
        TEXT link
        TEXT description
        TEXT language
        TEXT last_build_date
        TIMESTAMP updated_at
    }

    fetch_history {
        INTEGER id PK
        TIMESTAMP fetch_date
        INTEGER quotes_added
        INTEGER duplicates_skipped
        INTEGER total_processed
        TEXT status
    }

    quotes {
        INTEGER id PK
        TEXT author
        TEXT quote_text
        TEXT guid
        TEXT pub_date
        TEXT link
        TIMESTAMP created_at
    }

    quote_classifications {
        INTEGER id PK
        INTEGER quote_id FK
        TEXT category
        REAL confidence
        TEXT reasoning
        TIMESTAMP classified_at
    }

    quote_images {
        INTEGER id PK
        INTEGER quote_id FK
        TEXT image_path
        TIMESTAMP generated_at
    }

    telegram_uploads {
        INTEGER id PK
        INTEGER quote_id FK
        TEXT image_path
        INTEGER message_id
        TIMESTAMP uploaded_at
    }
```

---

## 7. Idempotency Model

```mermaid
flowchart TD
    A[quotes] --> B{classified?}
    B -- No --> C[classify]
    B -- Yes --> D{image exists?}
    D -- No --> E[generate image]
    D -- Yes --> F{uploaded?}
    F -- No --> G[upload to telegram]
    F -- Yes --> H[skip]
```

---

## 8. Data Integrity Rules

| Table                   | Rule                  |
| ----------------------- | --------------------- |
| `quotes`                | GUID is unique        |
| `quote_classifications` | One row per quote     |
| `quote_images`          | One image per quote   |
| `telegram_uploads`      | Exactly-once upload   |
| `fetch_history`         | Append-only audit log |

---

## 9. Failure Handling

| Failure          | Result                     |
| ---------------- | -------------------------- |
| Feed fetch fails | Logged in `fetch_history`  |
| Duplicate quote  | Skipped via `guid`         |
| LLM failure      | Quote remains unclassified |
| Image error      | Quote retried later        |
| Telegram error   | Upload retried safely      |

---

## 10. Deployment Model

* Docker Compose
* Each service is independently runnable
* SQLite shared via volume
* Ollama runs locally (GPU optional)

---

## 11. Architecture Status

**Version:** `0.1.0`
**Stability:** ✅ Stable
**Philosophy:**

> *State is truth. Tables define progress.*
