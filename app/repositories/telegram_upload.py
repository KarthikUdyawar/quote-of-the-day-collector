# app/repositories/telegram_upload.py
from sqlalchemy import select
from app.db.models import TelegramUpload
from app.db.session import get_db
from app.repositories.base import AsyncRepositoryBase
from typing import List


class TelegramUploadRepository(AsyncRepositoryBase[TelegramUpload]):
    def __init__(self):
        """
        Initialize the repository configured for TelegramUpload entities.
        
        Configures the base asynchronous repository to operate on the TelegramUpload model.
        """
        super().__init__(TelegramUpload)

    async def get_by_quote_id(self, quote_id: int) -> List[TelegramUpload]:
        """
        Retrieve TelegramUpload records for a quote, ordered by most recent upload first.
        
        Parameters:
        	quote_id (int): Identifier of the quote whose uploads to retrieve.
        
        Returns:
        	List[TelegramUpload]: TelegramUpload instances for the given quote ordered by `uploaded_at` descending.
        """
        async with get_db() as session:
            stmt = (
                select(self.model)
                .where(self.model.quote_id == quote_id)
                .order_by(self.model.uploaded_at.desc())
            )
            result = await session.scalars(stmt)
            return list(result.all())