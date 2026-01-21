# app/db/base.py
from typing import Type, TypeVar, Generic, Sequence
from sqlalchemy import select
from app.db.session import get_db

T = TypeVar("T")

class AsyncRepositoryBase(Generic[T]):
    def __init__(self, model: Type[T]):
        """
        Initialize the repository with the ORM model type.
        
        Parameters:
            model (Type[T]): ORM model class that this repository will operate on.
        """
        self.model = model

    async def add(self, obj: T) -> T:
        """
        Add an ORM instance to the database session and flush pending changes.
        
        Parameters:
            obj (T): ORM model instance to persist.
        
        Returns:
            T: The same instance after being added to the session; database-generated defaults (e.g., primary key) may be populated after flush.
        """
        async with get_db() as session:
            session.add(obj)
            await session.flush()
            return obj

    async def get(self, obj_id: int) -> T | None:
        """
        Retrieve a model instance by its primary key.
        
        Parameters:
            obj_id (int): Primary key value of the model to retrieve.
        
        Returns:
            T | None: The model instance with the given primary key, or None if no matching record exists.
        """
        async with get_db() as session:
            return await session.get(self.model, obj_id)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """
        Return a sequence of model instances from the database using the provided offset and limit.
        
        Parameters:
            limit (int): Maximum number of records to return. Defaults to 100.
            offset (int): Number of records to skip before returning results. Defaults to 0.
        
        Returns:
            Sequence[T]: A sequence of ORM model instances of type `T`.
        """
        async with get_db() as session:
            stmt = select(self.model).offset(offset).limit(limit)
            result = await session.scalars(stmt)
            return result.all()

    async def delete(self, obj: T) -> None:
        """
        Remove the given ORM model instance from the database session.
        
        Parameters:
            obj (T): An instance of the repository's model to delete from the database.
        """
        async with get_db() as session:
            await session.delete(obj)

    async def update(self, obj: T) -> T:
        """
        Merge the given ORM instance into the current database session and return the attached instance.
        
        Parameters:
            obj (T): ORM model instance to merge into the session.
        
        Returns:
            T: The instance attached to the session after merging.
        """
        async with get_db() as session:
            return await session.merge(obj)