"""Core service coordinating sports complex, court, and booking operations.

Encapsulates key business rules:
- Entity validation (complex hours, court pricing, ISO dates).
- Operating-hours enforcement.
- Double-booking and time-slot overlap prevention.
- Booking price calculation.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import uuid4

from reservapp.domain.exceptions import (
    EntityNotFoundError,
    InvalidDataError,
    SlotUnavailableError,
)
from reservapp.domain.models import (
    Booking,
    BookingStatus,
    Court,
    CourtType,
    SportsComplex,
)
from reservapp.repositories.base import BaseRepository


def _generate_id(prefix: str) -> str:
    """Generate a short human-readable identifier, e.g. `cmp-a1b2c3`."""
    return f"{prefix}-{uuid4().hex[:6]}"


def _validate_iso_date(date_str: str) -> str:
    """Validate that a date string follows ISO format YYYY-MM-DD."""
    try:
        date.fromisoformat(date_str)
    except ValueError as exc:
        raise InvalidDataError(
            f"Invalid date '{date_str}'. Expected ISO format YYYY-MM-DD (e.g., 2026-11-25)."
        ) from exc
    return date_str


class BookingService:
    """Orchestrates management of sports complexes, courts, and reservations."""

    def __init__(self, repository: BaseRepository) -> None:
        self._repo = repository

    # --- Sports complex management (Owners) ---

    def register_complex(
        self,
        name: str,
        address: str,
        owner_name: str,
        opening_hour: int = 8,
        closing_hour: int = 23,
        phone: str = "",
    ) -> SportsComplex:
        """Register a new sports complex after validating its operating hours."""
        name = name.strip()
        address = address.strip()
        owner_name = owner_name.strip()

        if not name or not address or not owner_name:
            raise InvalidDataError("Complex name, address, and owner name are required.")
        if not (0 <= opening_hour < closing_hour <= 24):
            raise InvalidDataError(
                "Operating hours must satisfy: 0 <= opening_hour < closing_hour <= 24."
            )

        sports_complex = SportsComplex(
            id=_generate_id("cmp"),
            name=name,
            address=address,
            owner_name=owner_name,
            opening_hour=opening_hour,
            closing_hour=closing_hour,
            phone=phone.strip(),
        )
        self._repo.save_complex(sports_complex)
        return sports_complex

    def list_complexes(self) -> list[SportsComplex]:
        """Return all registered sports complexes."""
        return self._repo.list_complexes()

    def get_complex(self, complex_id: str) -> SportsComplex:
        """Return a sports complex by ID or raise EntityNotFoundError."""
        sports_complex = self._repo.get_complex(complex_id)
        if sports_complex is None:
            raise EntityNotFoundError(f"Sports complex '{complex_id}' was not found.")
        return sports_complex

    # --- Court management (Owners) ---

    def add_court(
        self,
        complex_id: str,
        name: str,
        court_type: CourtType,
        hourly_rate: float,
        is_indoor: bool = False,
    ) -> Court:
        """Add a bookable court to an existing sports complex."""
        self.get_complex(complex_id)

        name = name.strip()
        if not name:
            raise InvalidDataError("Court name is required.")
        if hourly_rate <= 0:
            raise InvalidDataError("Hourly rate must be greater than zero.")

        court = Court(
            id=_generate_id("crt"),
            complex_id=complex_id,
            name=name,
            court_type=court_type,
            hourly_rate=float(hourly_rate),
            is_indoor=is_indoor,
            is_active=True,
        )
        self._repo.save_court(court)
        return court

    def list_courts_for_complex(self, complex_id: str) -> list[Court]:
        """Return all courts belonging to a given sports complex."""
        self.get_complex(complex_id)
        return self._repo.list_courts(complex_id=complex_id)

    def get_court(self, court_id: str) -> Court:
        """Return a court by ID or raise EntityNotFoundError."""
        court = self._repo.get_court(court_id)
        if court is None:
            raise EntityNotFoundError(f"Court '{court_id}' was not found.")
        return court

    # --- Availability and bookings (Players & Owners) ---

    def get_available_slots(self, court_id: str, booking_date: str) -> list[int]:
        """Return free 1-hour start hours (0-23) for a court on a given date."""
        _validate_iso_date(booking_date)
        court = self.get_court(court_id)
        if not court.is_active:
            return []

        sports_complex = self.get_complex(court.complex_id)
        day_bookings = self._repo.list_bookings(court_id=court_id, booking_date=booking_date)

        available_hours: list[int] = []
        for hour in range(sports_complex.opening_hour, sports_complex.closing_hour):
            is_taken = any(booking.overlaps_with(booking_date, hour, 1) for booking in day_bookings)
            if not is_taken:
                available_hours.append(hour)
        return available_hours

    def create_booking(
        self,
        court_id: str,
        customer_name: str,
        customer_phone: str,
        booking_date: str,
        start_hour: int,
        duration_hours: int = 1,
    ) -> Booking:
        """Create a confirmed booking after validating hours and slot availability."""
        _validate_iso_date(booking_date)
        customer_name = customer_name.strip()
        customer_phone = customer_phone.strip()

        if not customer_name:
            raise InvalidDataError("Customer name is required.")
        if duration_hours < 1 or duration_hours > 6:
            raise InvalidDataError("Booking duration must be between 1 and 6 hours.")

        court = self.get_court(court_id)
        if not court.is_active:
            raise SlotUnavailableError(f"Court '{court.name}' is currently inactive.")

        sports_complex = self.get_complex(court.complex_id)
        end_hour = start_hour + duration_hours
        if start_hour < sports_complex.opening_hour or end_hour > sports_complex.closing_hour:
            raise SlotUnavailableError(
                f"Requested range {start_hour:02d}:00-{end_hour:02d}:00 is outside "
                f"complex hours ({sports_complex.opening_hour:02d}:00-{sports_complex.closing_hour:02d}:00)."
            )

        existing_bookings = self._repo.list_bookings(court_id=court_id, booking_date=booking_date)
        for existing in existing_bookings:
            if existing.overlaps_with(booking_date, start_hour, duration_hours):
                raise SlotUnavailableError(
                    f"Court '{court.name}' is already booked from "
                    f"{existing.start_hour:02d}:00 to {existing.end_hour:02d}:00."
                )

        booking = Booking(
            id=_generate_id("bkg"),
            court_id=court_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            date=booking_date,
            start_hour=start_hour,
            duration_hours=duration_hours,
            total_price=court.hourly_rate * duration_hours,
            status=BookingStatus.CONFIRMED,
        )
        self._repo.save_booking(booking)
        return booking

    def cancel_booking(self, booking_id: str) -> Booking:
        """Cancel a confirmed booking and free its time slot."""
        booking = self._repo.get_booking(booking_id)
        if booking is None:
            raise EntityNotFoundError(f"Booking '{booking_id}' was not found.")
        if booking.status == BookingStatus.CANCELLED:
            raise InvalidDataError(f"Booking '{booking_id}' is already cancelled.")

        booking.status = BookingStatus.CANCELLED
        self._repo.save_booking(booking)
        return booking

    def list_bookings(
        self,
        court_id: Optional[str] = None,
        booking_date: Optional[str] = None,
        active_only: bool = False,
    ) -> list[Booking]:
        """Return bookings filtered by court, date, and optional active status."""
        if booking_date is not None:
            _validate_iso_date(booking_date)
        bookings = self._repo.list_bookings(court_id=court_id, booking_date=booking_date)
        if active_only:
            return [booking for booking in bookings if booking.is_active()]
        return bookings

    def seed_sample_data(self) -> bool:
        """Populate sample complexes and courts if the repository is empty."""
        if self._repo.list_complexes():
            return False

        arena = self.register_complex(
            name="Arena Gol Norte",
            address="Av. Principal 450",
            owner_name="Carlos Mendoza",
            opening_hour=8,
            closing_hour=23,
            phone="555-0101",
        )
        self.add_court(
            complex_id=arena.id,
            name="Cancha 1 - Sintética Techada",
            court_type=CourtType.SOCCER_5,
            hourly_rate=35.0,
            is_indoor=True,
        )
        self.add_court(
            complex_id=arena.id,
            name="Cancha 2 - Abierta",
            court_type=CourtType.SOCCER_7,
            hourly_rate=50.0,
            is_indoor=False,
        )

        club = self.register_complex(
            name="Complejo Deportivo El Parque",
            address="Calle 12 #8-20",
            owner_name="Laura Gómez",
            opening_hour=7,
            closing_hour=22,
            phone="555-0202",
        )
        self.add_court(
            complex_id=club.id,
            name="Pista Pádel Central",
            court_type=CourtType.PADEL,
            hourly_rate=28.0,
            is_indoor=True,
        )
        return True
