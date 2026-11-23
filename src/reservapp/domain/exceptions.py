"""Custom domain exceptions.

Separating domain exceptions allows both the current CLI and future interfaces
(such as a FastAPI REST API) to translate errors cleanly into user-friendly
messages or HTTP status codes (400, 404, 409).
"""


class ReservAppError(Exception):
    """Base exception for all business rule violations."""


class EntityNotFoundError(ReservAppError):
    """Raised when a requested complex, court, or booking does not exist."""


class SlotUnavailableError(ReservAppError):
    """Raised when a requested time slot overlaps another booking or is out of hours."""


class InvalidDataError(ReservAppError):
    """Raised when provided input violates domain validation rules."""
