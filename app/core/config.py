from pathlib import Path
import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env file only if it exists (safer for CI/tests/deploy)
env_path = BASE_DIR / ".env"
if env_path.is_file():
    load_dotenv(env_path)


class Config:
    def __init__(self):
        self._config: Dict[str, Any] = self._load_yaml()
        self._apply_env_overrides()
        self._validate()

    def _load_yaml(self) -> Dict[str, Any]:
        config_path = BASE_DIR / "config" / "base.yaml"
        if not config_path.is_file():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("Root of YAML config must be a dictionary")
            return data

    def _apply_env_overrides(self) -> None:
        # Telegram (most common override)
        telegram = self._config.setdefault("telegram", {})
        if token := os.getenv("TELEGRAM_BOT_TOKEN"):
            telegram["bot_token"] = token
        if chat_id := os.getenv("TELEGRAM_CHAT_ID"):
            telegram["chat_id"] = chat_id

        # Database engine override
        if engine := os.getenv("DB_ENGINE"):
            self._config.setdefault("database", {})["engine"] = engine.lower()

    def _validate(self) -> None:
        if "database" not in self._config:
            raise ValueError("Missing 'database' section in configuration")

        engine = self.database.get("engine", "sqlite").lower()
        if engine not in ("sqlite", "postgresql", "postgres"):
            raise ValueError(f"Unsupported database engine: {engine}")

    @property
    def database(self) -> Dict[str, Any]:
        return self._config["database"]

    @property
    def telegram(self) -> Dict[str, Any]:
        return self._config.get("telegram", {})

    @property
    def ollama(self) -> Dict[str, Any]:
        return self._config.get("ollama", {})

    @property
    def app(self) -> Dict[str, Any]:
        return self._config.get("app", {})


# For convenient import — but prefer dependency injection in larger apps
config = Config()
