from abc import ABC, abstractmethod

class Database(ABC):

    @abstractmethod
    def connect(self):
        ...

    @abstractmethod
    def execute(self, query: str, params: tuple = ()):
        ...

    @abstractmethod
    def fetchone(self):
        ...

    @abstractmethod
    def fetchall(self):
        ...

    @abstractmethod
    def commit(self):
        ...

    @abstractmethod
    def close(self):
        ...
