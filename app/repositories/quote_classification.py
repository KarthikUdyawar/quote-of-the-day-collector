# app/repositories/quote_classification.py
from sqlalchemy import select
from app.db.models import QuoteClassification
from app.db.session import get_db
from app.repositories.base import AsyncRepositoryBase
from typing import List


class QuoteClassificationRepository(AsyncRepositoryBase[QuoteClassification]):
    def __init__(self):
        super().__init__(QuoteClassification)

    async def get_by_quote_id(self, quote_id: int) -> List[QuoteClassification]:
        """Return all classifications for a quote."""
        async with get_db() as session:
            stmt = (
                select(self.model)
                .where(self.model.quote_id == quote_id)
                .order_by(self.model.classified_at.desc())
            )
            result = await session.scalars(stmt)
            return list(result.all())
