# app/repositories/fetch_history.py
from app.db.models import FetchHistory
from app.db.session import get_db
from app.repositories.base import AsyncRepositoryBase
from sqlalchemy import select

class FetchHistoryRepository(AsyncRepositoryBase[FetchHistory]):
    def __init__(self):
        super().__init__(FetchHistory)

    async def get_recent(self, limit: int = 10) -> list[FetchHistory]:
        """Return the most recent fetch history entries."""
        async with get_db() as session:
            stmt = select(self.model).order_by(self.model.fetch_date.desc()).limit(limit)
            result = await session.scalars(stmt)
            return list(result.all())
