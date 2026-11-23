"""Standard-library repository implementations.

- `InMemoryRepository`: fast, isolated storage ideal for unit tests.
- `JsonRepository`: persists state to a local JSON file across sessions.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from reservapp.domain.models import (
    Booking,
    BookingStatus,
    Court,
    CourtType,
    SportsComplex,
)
from reservapp.repositories.base import BaseRepository


class InMemoryRepository(BaseRepository):
    """Stores all domain entities in memory."""

    def __init__(self) -> None:
        self._complexes: dict[str, SportsComplex] = {}
        self._courts: dict[str, Court] = {}
        self._bookings: dict[str, Booking] = {}

    def save_complex(self, sports_complex: SportsComplex) -> None:
        self._complexes[sports_complex.id] = sports_complex

    def get_complex(self, complex_id: str) -> Optional[SportsComplex]:
        return self._complexes.get(complex_id)

    def list_complexes(self) -> list[SportsComplex]:
        return list(self._complexes.values())

    def save_court(self, court: Court) -> None:
        self._courts[court.id] = court

    def get_court(self, court_id: str) -> Optional[Court]:
        return self._courts.get(court_id)

    def list_courts(self, complex_id: Optional[str] = None) -> list[Court]:
        courts = list(self._courts.values())
        if complex_id is not None:
            return [court for court in courts if court.complex_id == complex_id]
        return courts

    def save_booking(self, booking: Booking) -> None:
        self._bookings[booking.id] = booking

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        return self._bookings.get(booking_id)

    def list_bookings(
        self,
        court_id: Optional[str] = None,
        booking_date: Optional[str] = None,
    ) -> list[Booking]:
        results = list(self._bookings.values())
        if court_id is not None:
            results = [booking for booking in results if booking.court_id == court_id]
        if booking_date is not None:
            results = [booking for booking in results if booking.date == booking_date]
        return sorted(results, key=lambda booking: (booking.date, booking.start_hour))


class JsonRepository(InMemoryRepository):
    """Extends `InMemoryRepository` by persisting every write to a JSON file."""

    def __init__(self, file_path: Path) -> None:
        super().__init__()
        self._file_path = Path(file_path)
        self._load()

    def _load(self) -> None:
        if not self._file_path.exists():
            return
        with self._file_path.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)

        for item in data.get("complexes", []):
            sports_complex = SportsComplex(**item)
            self._complexes[sports_complex.id] = sports_complex

        for item in data.get("courts", []):
            court = Court(
                id=item["id"],
                complex_id=item["complex_id"],
                name=item["name"],
                court_type=CourtType(item["court_type"]),
                hourly_rate=float(item["hourly_rate"]),
                is_indoor=bool(item.get("is_indoor", False)),
                is_active=bool(item.get("is_active", True)),
            )
            self._courts[court.id] = court

        for item in data.get("bookings", []):
            booking = Booking(
                id=item["id"],
                court_id=item["court_id"],
                customer_name=item["customer_name"],
                customer_phone=item["customer_phone"],
                date=item["date"],
                start_hour=int(item["start_hour"]),
                duration_hours=int(item.get("duration_hours", 1)),
                total_price=float(item.get("total_price", 0.0)),
                status=BookingStatus(item.get("status", BookingStatus.CONFIRMED.value)),
                created_at=item.get("created_at", ""),
            )
            self._bookings[booking.id] = booking

    def _persist(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "complexes": [asdict(item) for item in self._complexes.values()],
            "courts": [
                {**asdict(item), "court_type": item.court_type.value}
                for item in self._courts.values()
            ],
            "bookings": [
                {**asdict(item), "status": item.status.value}
                for item in self._bookings.values()
            ],
        }
        with self._file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, indent=2, ensure_ascii=False)

    def save_complex(self, sports_complex: SportsComplex) -> None:
        super().save_complex(sports_complex)
        self._persist()

    def save_court(self, court: Court) -> None:
        super().save_court(court)
        self._persist()

    def save_booking(self, booking: Booking) -> None:
        super().save_booking(booking)
        self._persist()
