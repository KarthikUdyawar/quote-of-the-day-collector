from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
import os
from app.core.config import config


def get_database_url() -> str:
    """
    Builds the async SQLAlchemy database URL from configuration and environment variables.
    
    Depending on the configured database engine, returns either a file-based SQLite URL using aiosqlite or a PostgreSQL URL using asyncpg. For SQLite, the path is taken from configuration and made relative to the application base directory when appropriate. For PostgreSQL, credentials must be provided via the DB_USER and DB_PASSWORD environment variables; host, port, and database name are read from DB_HOST, DB_PORT, and DB_NAME with sensible defaults.
    
    Returns:
        str: A database URL suitable for SQLAlchemy async engines (e.g. "sqlite+aiosqlite:///path/to/db" or "postgresql+asyncpg://user:pass@host:port/dbname").
    
    Raises:
        ValueError: If DB_USER or DB_PASSWORD are missing when PostgreSQL is selected, or if the configured engine is unsupported.
    """
    db_cfg = config.database
    engine_type = db_cfg.get("engine", "sqlite").lower()

    if engine_type == "sqlite":
        # Default can stay in code or config — no sensitive data
        db_path = db_cfg.get("path", "data/quotes.db")
        # Make sure it's relative to project root or absolute
        if not db_path.startswith(("/", ".")):
            db_path = f"{config.app.get('base_dir', '.')}/{db_path}"
        return f"sqlite+aiosqlite:///{db_path}"

    if engine_type in ("postgresql", "postgres"):
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "quotes")

        if not user or not password:
            raise ValueError(
                "PostgreSQL requires DB_USER and DB_PASSWORD environment variables.\n"
                "Example:\n"
                "  export DB_USER=quotes_user\n"
                "  export DB_PASSWORD=super-secret-value\n"
                "  export DB_NAME=quotes\n"
                "  export DB_HOST=localhost\n"
            )

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"

    raise ValueError(f"Unsupported database engine: {engine_type!r}")


engine: AsyncEngine = create_async_engine(
    get_database_url(),
    echo=config.database.get("echo", False),
    pool_pre_ping=True,
    # Sensible production-ish defaults (adjust as needed)
    pool_size=10,
    max_overflow=15,
    pool_timeout=30,
    pool_recycle=600,           # recycle connections every 10 min
)