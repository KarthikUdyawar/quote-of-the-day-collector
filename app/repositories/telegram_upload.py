# app/repositories/telegram_upload.py
from sqlalchemy import select
from app.db.models import TelegramUpload
from app.db.session import get_db
from app.repositories.base import AsyncRepositoryBase
from typing import List


class TelegramUploadRepository(AsyncRepositoryBase[TelegramUpload]):
    def __init__(self):
        super().__init__(TelegramUpload)

    async def get_by_quote_id(self, quote_id: int) -> List[TelegramUpload]:
        """Retrieve all Telegram uploads for a specific quote."""
        async with get_db() as session:
            stmt = (
                select(self.model)
                .where(self.model.quote_id == quote_id)
                .order_by(self.model.uploaded_at.desc())
            )
            result = await session.scalars(stmt)
            return list(result.all())
