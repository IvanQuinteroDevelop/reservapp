"""Abstract persistence contract.

Using an Abstract Base Class (ABC) decouples business logic from the storage
engine, making it straightforward to migrate from JSON to SQLite or PostgreSQL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from reservapp.domain.models import Booking, Court, SportsComplex


class BaseRepository(ABC):
    """Interface that any storage repository implementation must fulfill."""

    @abstractmethod
    def save_complex(self, sports_complex: SportsComplex) -> None:
        """Create or update a sports complex."""

    @abstractmethod
    def get_complex(self, complex_id: str) -> Optional[SportsComplex]:
        """Return a sports complex by ID, or None if not found."""

    @abstractmethod
    def list_complexes(self) -> list[SportsComplex]:
        """Return all registered sports complexes."""

    @abstractmethod
    def save_court(self, court: Court) -> None:
        """Create or update a court."""

    @abstractmethod
    def get_court(self, court_id: str) -> Optional[Court]:
        """Return a court by ID, or None if not found."""

    @abstractmethod
    def list_courts(self, complex_id: Optional[str] = None) -> list[Court]:
        """Return all courts, optionally filtered by sports complex ID."""

    @abstractmethod
    def save_booking(self, booking: Booking) -> None:
        """Create or update a booking."""

    @abstractmethod
    def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Return a booking by ID, or None if not found."""

    @abstractmethod
    def list_bookings(
        self,
        court_id: Optional[str] = None,
        booking_date: Optional[str] = None,
    ) -> list[Booking]:
        """List bookings optionally filtered by court ID and/or ISO date."""
