from app.core.config import config
from app.db.sqlite import SQLiteDatabase


def get_db():
    engine = config.database["engine"]

    if engine == "sqlite":
        db = SQLiteDatabase()
        db.connect()
        return db

    raise ValueError(f"Unsupported DB engine: {engine}")
