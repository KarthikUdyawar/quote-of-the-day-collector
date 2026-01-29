# app/db/async_session.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.db.engine import engine

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional async context manager that yields an AsyncSession.

    Yields an AsyncSession to the caller. Commits the session after successful use; if an exception occurs, rolls back the session and re-raises the exception.

    Returns:
        AsyncGenerator[AsyncSession, None]: A generator that yields an AsyncSession for use in an `async with` block.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
