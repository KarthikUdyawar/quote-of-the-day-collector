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
        """
        Initialize the Config instance by loading configuration from the base YAML file, applying environment variable overrides, and validating the resulting configuration.
        
        Raises:
            FileNotFoundError: if the base YAML configuration file does not exist.
            ValueError: if the loaded configuration is not a mapping or the database configuration is missing/contains an unsupported engine.
        """
        self._config: Dict[str, Any] = self._load_yaml()
        self._apply_env_overrides()
        self._validate()

    def _load_yaml(self) -> Dict[str, Any]:
        """
        Load and parse the project's base YAML configuration at BASE_DIR/config/base.yaml.
        
        Returns:
            dict: The parsed top-level mapping of the configuration.
        
        Raises:
            FileNotFoundError: If the config file does not exist at BASE_DIR/config/base.yaml.
            ValueError: If the YAML root node is not a mapping (dictionary).
        """
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
        """
        Apply environment variable overrides to the configuration.
        
        If present, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID populate config["telegram"]["bot_token"] and config["telegram"]["chat_id"], respectively. If DB_ENGINE is present, its lowercased value is assigned to config["database"]["engine"]. Ensures "telegram" and "database" mappings exist before applying overrides.
        """
        telegram = self._config.setdefault("telegram", {})
        if token := os.getenv("TELEGRAM_BOT_TOKEN"):
            telegram["bot_token"] = token
        if chat_id := os.getenv("TELEGRAM_CHAT_ID"):
            telegram["chat_id"] = chat_id

        # Database engine override
        if engine := os.getenv("DB_ENGINE"):
            self._config.setdefault("database", {})["engine"] = engine.lower()

    def _validate(self) -> None:
        """
        Validate that the configuration includes a database section and that the database engine is supported.
        
        Raises:
            ValueError: If the 'database' section is missing or if the database engine is not one of "sqlite", "postgresql", or "postgres".
        """
        if "database" not in self._config:
            raise ValueError("Missing 'database' section in configuration")

        engine = self.database.get("engine", "sqlite").lower()
        if engine not in ("sqlite", "postgresql", "postgres"):
            raise ValueError(f"Unsupported database engine: {engine}")

    @property
    def database(self) -> Dict[str, Any]:
        """
        Access the application's database configuration.
        
        Returns:
            dict: Database configuration mapping (for example, `engine` and connection parameters).
        """
        return self._config["database"]

    @property
    def telegram(self) -> Dict[str, Any]:
        """
        Return the Telegram configuration section.
        
        Returns:
            Dict[str, Any]: Telegram configuration mapping containing keys like `bot_token` and `chat_id`; empty dict if the section is absent.
        """
        return self._config.get("telegram", {})

    @property
    def ollama(self) -> Dict[str, Any]:
        """
        Get the Ollama configuration mapping.
        
        Returns:
            The `ollama` configuration mapping from the loaded configuration, or an empty dict if not present.
        """
        return self._config.get("ollama", {})

    @property
    def app(self) -> Dict[str, Any]:
        """
        Retrieve the application's configuration mapping.
        
        Returns:
            dict: The app configuration dictionary from the loaded config, or an empty dict if not present.
        """
        return self._config.get("app", {})


# For convenient import — but prefer dependency injection in larger apps
config = Config()