# app/repositories/quote.py
from sqlalchemy import select
from typing import List
from app.db.models import Quote
from app.repositories.base import AsyncRepositoryBase
from app.db.session import get_db  # ✅ import directly

class QuoteRepository(AsyncRepositoryBase[Quote]):
    def __init__(self):
        """
        Initialize the repository bound to the Quote model.
        """
        super().__init__(Quote)

    async def exists_by_guid(self, guid: str) -> bool:
        """
        Check whether a Quote with the specified GUID exists.
        
        Parameters:
            guid (str): GUID of the quote to check.
        
        Returns:
            bool: `true` if a matching Quote exists, `false` otherwise.
        """
        async with get_db() as session:  # ✅ use get_db() directly
            stmt = select(self.model).where(self.model.guid == guid)
            result = await session.scalars(stmt)
            return result.first() is not None

    async def get_by_author(self, author: str, limit: int = 50) -> List[Quote]:
        """
        Retrieve quotes for a specific author ordered by most recent publication.
        
        Parameters:
        	author (str): Exact author name to filter quotes.
        	limit (int): Maximum number of quotes to return.
        
        Returns:
        	List[Quote]: Quotes authored by `author`, ordered by `pub_date` descending, limited to `limit`.
        """
        async with get_db() as session:
            stmt = (
                select(self.model)
                .where(self.model.author == author)
                .order_by(self.model.pub_date.desc())
                .limit(limit)
            )
            result = await session.scalars(stmt)
            return list(result.all())

    async def search_quotes(self, keyword: str, limit: int = 50) -> List[Quote]:
        """
        Retrieve quotes whose text contains the given keyword (case-insensitive), ordered by publication date descending.
        
        Parameters:
            keyword (str): Substring to search for within quote text, matched case-insensitively.
            limit (int): Maximum number of quotes to return.
        
        Returns:
            List[Quote]: Quotes matching the keyword, ordered newest first. Returns an empty list if no matches are found.
        """
        async with get_db() as session:
            stmt = (
                select(self.model)
                .where(self.model.quote_text.ilike(f"%{keyword}%"))
                .order_by(self.model.pub_date.desc())
                .limit(limit)
            )
            result = await session.scalars(stmt)
            return list(result.all())

    async def get_recent(self, limit: int = 10) -> List[Quote]:
        """
        Retrieve recent Quote records ordered by publication date descending.
        
        Parameters:
            limit (int): Maximum number of quotes to return.
        
        Returns:
            List[Quote]: A list of Quote objects ordered from newest to oldest, containing at most `limit` items.
        """
        async with get_db() as session:
            stmt = select(self.model).order_by(self.model.pub_date.desc()).limit(limit)
            result = await session.scalars(stmt)
            return list(result.all())

    async def total_count(self) -> int:
        """
        Get the total number of records for the repository's model.
        
        Returns:
            total (int): The number of model records in the database.
        """
        async with get_db() as session:
            stmt = select(self.model)
            result = await session.scalars(stmt)
            return len(list(result.all()))