# Quote of the Day Collector

<!-- Static badges -->
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)

<!-- Dynamic badges -->
![GitHub release](https://img.shields.io/github/v/release/KarthikUdyawar/quote-of-the-day-collector?color=brightgreen)
![GitHub issues](https://img.shields.io/github/issues/KarthikUdyawar/quote-of-the-day-collector)
![GitHub forks](https://img.shields.io/github/forks/KarthikUdyawar/quote-of-the-day-collector?style=social)
![GitHub stars](https://img.shields.io/github/stars/KarthikUdyawar/quote-of-the-day-collector?style=social)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)

Quote of the Day Collector is a **fully automated quote aggregation, classification, image generation, and Telegram publishing system**.
It fetches quotes, classifies them into subjects, generates branded quote images, and uploads them to a Telegram channel — all backed by SQLite and Dockerized services.

---

## ✨ Features

* 📥 Fetches quotes from external sources
* 🧠 Classifies quotes into meaningful categories
* 🖼️ Generates quote images using Pillow
* 📤 Uploads images to Telegram with formatted captions
* 🗃️ SQLite-based persistent storage
* 🐳 Dockerized micro-services
* 📊 Upload tracking & statistics
* 📝 Detailed logging per service

---

## 🏗️ Architecture Overview

The system is designed as **loosely coupled services**, each responsible for one stage of the pipeline:

```
Quotes → Database → Classification → Image Generation → Telegram Upload
```

Each step is **idempotent** and tracked in the database to prevent duplicates.

---

## 📁 Project Structure

```
quote-of-the-day-collector
├── data/
│   └── quotes.db                 # SQLite database
├── images/                       # Generated quote images (category/date-based)
├── logs/                         # Service-specific logs
│   ├── quote_fetcher.log
│   ├── quote_classifier.log
│   ├── quote_image_generator.log
│   └── telegram_uploader.log
├── docker-compose.yml
├── Dockerfile.fetcher
├── Dockerfile.classifier
├── Dockerfile.image-generator
├── Dockerfile.telegram-uploader
├── quote_fetcher.py              # Fetches quotes
├── quote_classifier.py           # Classifies quotes by subject
├── quote_image_generator.py      # Generates quote images
├── telegram_uploader.py          # Uploads images to Telegram
├── pull-model.sh                 # Pulls ML models (if applicable)
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

## 📚 Documentation

* [ARCHITECTURE](ARCHITECTURE.md) – Detailed system architecture, database schema, and sequence diagrams  
* [CHANGELOG](CHANGELOG.md) – Version history and updates  
* [TELEGRAM_SETUP](TELEGRAM_SETUP.md) – How to obtain `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

---

## 🧠 Data Model (High Level)

The SQLite database (`data/quotes.db`) contains:

* `quotes` – quote text, author, GUID, and publication info
* `quote_classifications` – category, confidence, and reasoning per quote
* `feed_info` – metadata about each RSS feed
* `fetch_history` – history of fetch runs, including duplicates skipped
* `quote_images` – generated image paths
* `telegram_uploads` – upload tracking to prevent duplicates

---

## 🔐 Environment Variables

Create a `.env` file or export variables:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=@your_channel_or_chat_id
```

### How to get them

1. **Bot Token:**

   * Talk to [@BotFather](https://t.me/BotFather) on Telegram.
   * Create a new bot → copy the token.

2. **Chat ID:**

   * For a **channel**, use the channel username: `@mychannel`.
   * For a **group or personal chat**, use [@userinfobot](https://t.me/userinfobot):

     * Start a chat with `@userinfobot` and send `/start`
     * Copy the **ID** it returns as `TELEGRAM_CHAT_ID`.

---

## ⚙️ Installation (Local)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/KarthikUdyawar/quote-of-the-day-collector.git
cd quote-of-the-day-collector
```

### 2️⃣ Create virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
# OR
pip install .
```

---

## 🐳 Docker Setup (Recommended)

Run all services using Docker Compose:

```bash
docker-compose up --build
```

Each service runs independently and logs to `/logs`.

---

## 🚀 Usage

### Fetch Quotes

```bash
python quote_fetcher.py
```

### Classify Quotes

```bash
python quote_classifier.py
```

### Generate Quote Images

```bash
python quote_image_generator.py
```

Images are saved as:

```
images/<Category>/<DD-MM-YYYY>/quote_<id>_<Author>.png
```

### Upload to Telegram

#### Upload pending images

```bash
python telegram_uploader.py --action upload
```

#### Upload with batch limit

```bash
python telegram_uploader.py --batch-size 5
```

#### Test Telegram connection

```bash
python telegram_uploader.py --action test
```

#### View upload statistics

```bash
python telegram_uploader.py --action stats
```

---

## 🖼️ Telegram Caption Format

Uploaded images use **Markdown V2 formatting**:

```
*Quote text*

~ _Author_

#Category
```

Special characters are automatically escaped.

---

## 📊 Upload Tracking & Statistics

The uploader tracks:

* Total images
* Uploaded images
* Pending uploads
* Uploads by category
* Last upload timestamp

View stats with:

```bash
python telegram_uploader.py --action stats
```

---

## 📝 Logging

Each service writes logs to `logs/`:

* `quote_fetcher.log`
* `quote_classifier.log`
* `quote_image_generator.log`
* `telegram_uploader.log`

Logs are written to both **file and stdout**.

---

## 📦 Dependencies

Core dependencies (from `pyproject.toml`):

* `feedparser` – RSS & feed parsing
* `requests` – HTTP requests
* `pillow` – Image generation
* `python-telegram-bot` – Telegram API
* `dotenv` – Environment variable management
* `schedule` – Job scheduling

---

## 🔖 Versioning

This project follows **Semantic Versioning**.

* **0.1.0** – Initial stable pipeline (fetch → classify → image → upload)

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
