# app/services/fetch_history.py
from app.db.models import FetchHistory
from app.db.session import get_db
from app.services.base import AsyncServiceBase
from sqlalchemy import select


class FetchHistoryService(AsyncServiceBase[FetchHistory]):
    def __init__(self):
        """
        Initialize the service configured to operate on the FetchHistory model.
        """
        super().__init__(FetchHistory)

    async def get_recent(self, limit: int = 10) -> list[FetchHistory]:
        """
        Retrieve the most recent FetchHistory entries.

        Parameters:
            limit (int): Maximum number of entries to return.

        Returns:
            list[FetchHistory]: A list of FetchHistory instances ordered by `fetch_date` descending, limited to `limit` entries.
        """
        async with get_db() as session:
            stmt = (
                select(self.model).order_by(self.model.fetch_date.desc()).limit(limit)
            )
            result = await session.scalars(stmt)
            return list(result.all())
