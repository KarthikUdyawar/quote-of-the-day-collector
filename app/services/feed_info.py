# app//feed_info.py
from app.db.models import FeedInfo
from app.db.session import get_db
from app.services.base import AsyncServiceBase
from sqlalchemy import select


class FeedInfoService(AsyncServiceBase[FeedInfo]):
    def __init__(self):
        """
        Initialize the service configured for the FeedInfo model.

        Configures the base asynchronous service to operate on the FeedInfo ORM model.
        """
        super().__init__(FeedInfo)

    async def get_by_link(self, link: str) -> FeedInfo | None:
        """
        Retrieve a feed by its URL.

        Parameters:
            link (str): The feed URL to search for.

        Returns:
            The matching FeedInfo if found, `None` otherwise.
        """
        async with get_db() as session:
            stmt = select(self.model).where(self.model.link == link)
            result = await session.scalars(stmt)
            return result.first()
