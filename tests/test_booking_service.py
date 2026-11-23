"""Unit tests for BookingService and JsonRepository persistence.

Run with:
    .venv/bin/python -m unittest discover -s tests -v
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

# Allow running tests directly without installing the package first
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from reservapp.domain.exceptions import (  # noqa: E402
    EntityNotFoundError,
    InvalidDataError,
    SlotUnavailableError,
)
from reservapp.domain.models import BookingStatus, CourtType  # noqa: E402
from reservapp.repositories.json_repository import (  # noqa: E402
    InMemoryRepository,
    JsonRepository,
)
from reservapp.services.booking_service import BookingService  # noqa: E402


class TestBookingService(unittest.TestCase):
    """Verify core booking business rules."""

    def setUp(self) -> None:
        self.repo = InMemoryRepository()
        self.service = BookingService(self.repo)
        self.sports_complex = self.service.register_complex(
            name="El Golazo Arena",
            address="100 Sports Ave",
            owner_name="Ana Ruiz",
            opening_hour=9,
            closing_hour=22,
        )
        self.court = self.service.add_court(
            complex_id=self.sports_complex.id,
            name="Synthetic Court 1",
            court_type=CourtType.SOCCER_5,
            hourly_rate=40.0,
            is_indoor=True,
        )

    def test_create_booking_succeeds_and_calculates_price(self) -> None:
        booking = self.service.create_booking(
            court_id=self.court.id,
            customer_name="Mateo Silva",
            customer_phone="555-1234",
            booking_date="2026-12-01",
            start_hour=18,
            duration_hours=2,
        )

        self.assertEqual(booking.status, BookingStatus.CONFIRMED)
        self.assertEqual(booking.end_hour, 20)
        self.assertEqual(booking.total_price, 80.0)

    def test_rejects_overlapping_bookings(self) -> None:
        self.service.create_booking(
            court_id=self.court.id,
            customer_name="Mateo Silva",
            customer_phone="555-1234",
            booking_date="2026-12-01",
            start_hour=18,
            duration_hours=2,  # 18:00 - 20:00
        )

        with self.assertRaises(SlotUnavailableError):
            self.service.create_booking(
                court_id=self.court.id,
                customer_name="Sofia Castro",
                customer_phone="555-9999",
                booking_date="2026-12-01",
                start_hour=19,
                duration_hours=1,
            )

    def test_rejects_booking_outside_complex_operating_hours(self) -> None:
        with self.assertRaises(SlotUnavailableError):
            self.service.create_booking(
                court_id=self.court.id,
                customer_name="Lucas Perez",
                customer_phone="",
                booking_date="2026-12-01",
                start_hour=21,
                duration_hours=2,  # ends at 23:00, complex closes at 22:00
            )

    def test_cancelling_booking_releases_time_slot(self) -> None:
        booking = self.service.create_booking(
            court_id=self.court.id,
            customer_name="Mateo Silva",
            customer_phone="",
            booking_date="2026-12-01",
            start_hour=10,
            duration_hours=1,
        )
        self.assertNotIn(10, self.service.get_available_slots(self.court.id, "2026-12-01"))

        cancelled = self.service.cancel_booking(booking.id)
        self.assertEqual(cancelled.status, BookingStatus.CANCELLED)
        self.assertIn(10, self.service.get_available_slots(self.court.id, "2026-12-01"))

    def test_rejects_invalid_date_format(self) -> None:
        with self.assertRaises(InvalidDataError):
            self.service.get_available_slots(self.court.id, "01-12-2026")

    def test_raises_error_when_court_does_not_exist(self) -> None:
        with self.assertRaises(EntityNotFoundError):
            self.service.get_available_slots("crt-missing", "2026-12-01")


class TestJsonRepository(unittest.TestCase):
    """Verify data persists and reloads accurately on disk."""

    def test_persistence_across_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "reservapp_test.json"

            service_1 = BookingService(JsonRepository(db_path))
            sports_complex = service_1.register_complex("South Arena", "5th Street", "Diego")
            court = service_1.add_court(
                sports_complex.id, "Court A", CourtType.SOCCER_7, 60.0
            )
            booking = service_1.create_booking(
                court.id, "Elena", "555-7777", "2026-12-10", 17, 1
            )

            # New instance reading the same JSON file
            service_2 = BookingService(JsonRepository(db_path))
            complexes = service_2.list_complexes()
            bookings = service_2.list_bookings(court_id=court.id)

            self.assertEqual(len(complexes), 1)
            self.assertEqual(complexes[0].name, "South Arena")
            self.assertEqual(len(bookings), 1)
            self.assertEqual(bookings[0].id, booking.id)
            self.assertEqual(bookings[0].total_price, 60.0)


if __name__ == "__main__":
    unittest.main()
