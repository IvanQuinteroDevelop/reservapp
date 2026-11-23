"""Repository layer: persistence abstractions and concrete storage adapters."""

from .base import BaseRepository
from .json_repository import InMemoryRepository, JsonRepository

__all__ = ["BaseRepository", "InMemoryRepository", "JsonRepository"]
