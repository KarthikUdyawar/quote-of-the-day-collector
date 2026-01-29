# app/services/quote_classification.py
from sqlalchemy import select
from app.db.models import QuoteClassification
from app.db.session import get_db
from app.services.base import AsyncServiceBase
from typing import List


class QuoteClassificationService(AsyncServiceBase[QuoteClassification]):
    def __init__(self):
        """
        Initialize the service configured for the QuoteClassification model.

        Sets the service's model to QuoteClassification so the base CRUD operations target that model.
        """
        super().__init__(QuoteClassification)

    async def get_by_quote_id(self, quote_id: int) -> List[QuoteClassification]:
        """
        Retrieve all classifications for a given quote ordered by `classified_at` descending.

        Parameters:
            quote_id (int): The quote's primary key identifier.

        Returns:
            List[QuoteClassification]: List of QuoteClassification objects ordered from newest to oldest by `classified_at`.
        """
        async with get_db() as session:
            stmt = (
                select(self.model)
                .where(self.model.quote_id == quote_id)
                .order_by(self.model.classified_at.desc())
            )
            result = await session.scalars(stmt)
            return list(result.all())
