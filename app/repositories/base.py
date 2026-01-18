# app/db/base.py
from typing import Type, TypeVar, Generic, Sequence
from sqlalchemy import select
from app.db.session import get_db

T = TypeVar("T")

class AsyncRepositoryBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def add(self, obj: T) -> T:
        async with get_db() as session:
            session.add(obj)
            await session.flush()
            return obj

    async def get(self, obj_id: int) -> T | None:
        async with get_db() as session:
            return await session.get(self.model, obj_id)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        async with get_db() as session:
            stmt = select(self.model).offset(offset).limit(limit)
            result = await session.scalars(stmt)
            return result.all()

    async def delete(self, obj: T) -> None:
        async with get_db() as session:
            await session.delete(obj)

    async def update(self, obj: T) -> T:
        async with get_db() as session:
            return await session.merge(obj)