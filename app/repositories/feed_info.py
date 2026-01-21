# app/repositories/feed_info.py
from app.db.models import FeedInfo
from app.db.session import get_db
from app.repositories.base import AsyncRepositoryBase
from sqlalchemy import select

class FeedInfoRepository(AsyncRepositoryBase[FeedInfo]):
    def __init__(self):
        """
        Initialize the repository configured for the FeedInfo model.
        
        Configures the base asynchronous repository to operate on the FeedInfo ORM model.
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