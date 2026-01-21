# app/repositories/quote.py
from sqlalchemy import select
from typing import List
from app.db.models import Quote
from app.repositories.base import AsyncRepositoryBase
from app.db.session import get_db  # ✅ import directly

class QuoteRepository(AsyncRepositoryBase[Quote]):
    def __init__(self):
        super().__init__(Quote)

    async def exists_by_guid(self, guid: str) -> bool:
        """Check if a quote with the given GUID exists."""
        async with get_db() as session:  # ✅ use get_db() directly
            stmt = select(self.model).where(self.model.guid == guid)
            result = await session.scalars(stmt)
            return result.first() is not None

    async def get_by_author(self, author: str, limit: int = 50) -> List[Quote]:
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
        async with get_db() as session:
            stmt = select(self.model).order_by(self.model.pub_date.desc()).limit(limit)
            result = await session.scalars(stmt)
            return list(result.all())

    async def total_count(self) -> int:
        async with get_db() as session:
            stmt = select(self.model)
            result = await session.scalars(stmt)
            return len(list(result.all()))
