"""Core domain models for sports complexes, courts, and bookings.

Uses Python standard library `dataclass` and `Enum` to keep the business core
explicit, strongly typed, and independent of storage or UI layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CourtType(str, Enum):
    """Supported court and pitch categories."""

    SOCCER_5 = "soccer_5"
    SOCCER_7 = "soccer_7"
    SOCCER_11 = "soccer_11"
    PADEL = "padel"
    TENNIS = "tennis"
    BASKETBALL = "basketball"


class BookingStatus(str, Enum):
    """Lifecycle states for a court booking (extensible for payments/no-shows)."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass
class SportsComplex:
    """Represents a sports venue that manages one or more courts."""

    id: str
    name: str
    address: str
    owner_name: str
    opening_hour: int = 8
    closing_hour: int = 23
    phone: str = ""


@dataclass
class Court:
    """Represents an individual bookable court inside a sports complex."""

    id: str
    complex_id: str
    name: str
    court_type: CourtType
    hourly_rate: float
    is_indoor: bool = False
    is_active: bool = True


@dataclass
class Booking:
    """Represents a reservation for a court on a specific date and time range."""

    id: str
    court_id: str
    customer_name: str
    customer_phone: str
    date: str  # ISO format: YYYY-MM-DD
    start_hour: int  # Whole hour in 24h format (0-23)
    duration_hours: int = 1
    total_price: float = 0.0
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def end_hour(self) -> int:
        """Return the booking end hour."""
        return self.start_hour + self.duration_hours

    def is_active(self) -> bool:
        """Return True if the booking currently holds the time slot."""
        return self.status == BookingStatus.CONFIRMED

    def overlaps_with(self, booking_date: str, start_hour: int, duration_hours: int) -> bool:
        """Check whether another date/time range conflicts with this booking."""
        if not self.is_active() or self.date != booking_date:
            return False
        other_end_hour = start_hour + duration_hours
        return self.start_hour < other_end_hour and start_hour < self.end_hour
