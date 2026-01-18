import sqlite3
from app.db.base import Database
from app.core.config import config
from app.core.logging import log


class SQLiteDatabase(Database):
    def __init__(self):
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def connect(self):
        db_path = config.database["path"]
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        log.info(f"SQLite connected → {db_path}")

    def execute(self, query, params=()):
        if self.cursor is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.cursor.execute(query, params)

    def fetchone(self):
        if self.cursor is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.cursor.fetchone()

    def fetchall(self):
        if self.cursor is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.cursor.fetchall()

    def commit(self):
        if self.conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        self.conn.commit()

    def close(self):
        if self.conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        self.conn.close()
        log.info("SQLite connection closed")
        