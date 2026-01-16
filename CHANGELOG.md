# Changelog

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.1.0] - 2026-01-17

### Added

* **Quote Fetcher** (`quote_fetcher.py`)

  * Fetch quotes from RSS feeds.
  * Store feed metadata in `feed_info` table.
  * Store quotes in `quotes` table with duplicate prevention using `guid`.
  * Log fetch history in `fetch_history` table.
  * Scheduler to fetch periodically or run once.
* **Quote Image Generator** (`quote_image_generator.py`)

  * Generate Instagram-ready images for classified quotes.
  * Support category-based color themes.
  * Save generated images in `quote_images` table and structured folders (`images/<category>/<date>/`).
  * Dynamic font sizing and text wrapping.
  * CLI support for batch generation and statistics reporting.
* **Telegram Uploader** (`telegram_uploader.py`)

  * Upload quote images to Telegram channels.
  * Track uploads in `telegram_uploads` table.
  * Format captions with MarkdownV2.
  * Async support with rate-limit delay handling.
  * Test connection functionality.
* **Database Schema**

  * `feed_info` - stores feed metadata.
  * `quotes` - stores quotes with `guid` uniqueness.
  * `fetch_history` - logs fetch attempts.
  * `quote_classifications` - stores category classification and confidence.
  * `quote_images` - tracks generated images.
  * `telegram_uploads` - tracks Telegram uploads.
* **Project Configuration**

  * `pyproject.toml` with dependencies (`dotenv`, `feedparser`, `Pillow`, `python-telegram-bot`, `schedule`, `requests`).

### Changed

* N/A (initial release)

### Fixed

* N/A (initial release)

### Documentation

* **ARCHITECTURE.md**

  * Added detailed architecture overview.
  * Full database schema diagram including all tables.
  * End-to-end sequence diagram for the quote processing pipeline.
  * Component interaction description.
* **README.md**

  * Instructions for setup, usage, and CLI commands.

