from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


class Config:
    def __init__(self):
        self._config = self._load_yaml()
        self._apply_env_overrides()

    def _load_yaml(self):
        config_path = BASE_DIR / "config" / "base.yaml"
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _apply_env_overrides(self):
        # Telegram
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self._config.setdefault("telegram", {})
            self._config["telegram"]["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")

        if os.getenv("TELEGRAM_CHAT_ID"):
            self._config.setdefault("telegram", {})
            self._config["telegram"]["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")

        # Database override (future-proof)
        if os.getenv("DB_ENGINE"):
            self._config["database"]["engine"] = os.getenv("DB_ENGINE")

    @property
    def database(self):
        return self._config["database"]

    @property
    def telegram(self):
        return self._config.get("telegram", {})

    @property
    def ollama(self):
        return self._config.get("ollama", {})

    @property
    def app(self):
        return self._config.get("app", {})


# singleton-style access
config = Config()
