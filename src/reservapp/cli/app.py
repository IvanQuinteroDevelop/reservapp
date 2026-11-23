"""Interactive CLI for players and sports complex owners.

This layer is strictly responsible for user input and display formatting.
All code, identifiers, and comments are in English; only user-facing UI
strings are currently localized in Spanish (ready for future i18n support).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from reservapp.domain.exceptions import ReservAppError
from reservapp.domain.models import BookingStatus, Court, CourtType, SportsComplex
from reservapp.repositories.json_repository import JsonRepository
from reservapp.services.booking_service import BookingService

DEFAULT_DATA_PATH = Path("data") / "reservapp_db.json"

# Localized display labels for the Spanish CLI (easily replaceable with i18n catalogs)
COURT_TYPE_LABELS: dict[CourtType, str] = {
    CourtType.SOCCER_5: "Fútbol 5",
    CourtType.SOCCER_7: "Fútbol 7",
    CourtType.SOCCER_11: "Fútbol 11",
    CourtType.PADEL: "Pádel",
    CourtType.TENNIS: "Tenis",
    CourtType.BASKETBALL: "Baloncesto",
}

BOOKING_STATUS_LABELS: dict[BookingStatus, str] = {
    BookingStatus.CONFIRMED: "CONFIRMADA",
    BookingStatus.CANCELLED: "CANCELADA",
}


def _prompt_text(label: str, required: bool = True, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if not value and default:
            return default
        if value or not required:
            return value
        print("  -> Este campo es obligatorio.")


def _prompt_int(label: str, default: Optional[int] = None) -> int:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw_value = input(f"{label}{suffix}: ").strip()
        if not raw_value and default is not None:
            return default
        try:
            return int(raw_value)
        except ValueError:
            print("  -> Ingresa un número entero válido.")


def _prompt_float(label: str) -> float:
    while True:
        raw_value = input(f"{label}: ").strip().replace(",", ".")
        try:
            return float(raw_value)
        except ValueError:
            print("  -> Ingresa un valor numérico válido (ej. 35.50).")


def _select_complex(service: BookingService) -> Optional[SportsComplex]:
    complexes = service.list_complexes()
    if not complexes:
        print("\nNo hay complejos deportivos registrados todavía.")
        return None

    print("\nComplejos disponibles:")
    for index, sports_complex in enumerate(complexes, start=1):
        print(
            f"  {index}. {sports_complex.name} — {sports_complex.address} "
            f"({sports_complex.opening_hour:02d}:00 a {sports_complex.closing_hour:02d}:00) "
            f"[Dueño: {sports_complex.owner_name}]"
        )

    choice = _prompt_int("Elige el número del complejo (0 para cancelar)")
    if choice == 0:
        return None
    if 1 <= choice <= len(complexes):
        return complexes[choice - 1]
    print("  -> Selección fuera de rango.")
    return None


def _select_court(service: BookingService, sports_complex: SportsComplex) -> Optional[Court]:
    courts = service.list_courts_for_complex(sports_complex.id)
    if not courts:
        print(f"\nEl complejo '{sports_complex.name}' aún no tiene canchas registradas.")
        return None

    print(f"\nCanchas de '{sports_complex.name}':")
    for index, court in enumerate(courts, start=1):
        roof_label = "Techada" if court.is_indoor else "Al aire libre"
        type_label = COURT_TYPE_LABELS[court.court_type]
        print(
            f"  {index}. {court.name} | {type_label} | "
            f"{roof_label} | ${court.hourly_rate:.2f}/hora"
        )

    choice = _prompt_int("Elige el número de la cancha (0 para cancelar)")
    if choice == 0:
        return None
    if 1 <= choice <= len(courts):
        return courts[choice - 1]
    print("  -> Selección fuera de rango.")
    return None


def _select_court_type() -> CourtType:
    court_types = list(CourtType)
    print("\nTipos de cancha:")
    for index, court_type in enumerate(court_types, start=1):
        print(f"  {index}. {COURT_TYPE_LABELS[court_type]}")

    while True:
        choice = _prompt_int("Elige el tipo de cancha")
        if 1 <= choice <= len(court_types):
            return court_types[choice - 1]
        print("  -> Opción inválida.")


def _show_catalog(service: BookingService) -> None:
    complexes = service.list_complexes()
    if not complexes:
        print("\nAún no hay complejos registrados.")
        return

    print("\n=== CATÁLOGO DE COMPLEJOS Y CANCHAS ===")
    for sports_complex in complexes:
        print(
            f"\n[{sports_complex.id}] {sports_complex.name} "
            f"({sports_complex.opening_hour:02d}:00-{sports_complex.closing_hour:02d}:00)"
        )
        print(
            f"  Dirección: {sports_complex.address} | "
            f"Dueño: {sports_complex.owner_name} | "
            f"Tel: {sports_complex.phone or 'N/A'}"
        )
        courts = service.list_courts_for_complex(sports_complex.id)
        if not courts:
            print("  (Sin canchas registradas)")
            continue
        for court in courts:
            roof_label = "Techada" if court.is_indoor else "Abierta"
            type_label = COURT_TYPE_LABELS[court.court_type]
            print(
                f"  - [{court.id}] {court.name} | {type_label} | "
                f"{roof_label} | ${court.hourly_rate:.2f}/h"
            )


def _check_availability(service: BookingService) -> None:
    sports_complex = _select_complex(service)
    if sports_complex is None:
        return
    court = _select_court(service, sports_complex)
    if court is None:
        return

    booking_date = _prompt_text("Fecha (AAAA-MM-DD)", default=date.today().isoformat())
    slots = service.get_available_slots(court.id, booking_date)

    if not slots:
        print(f"\nNo hay horarios disponibles para '{court.name}' el {booking_date}.")
        return

    formatted_slots = ", ".join(f"{hour:02d}:00" for hour in slots)
    print(f"\nHorarios disponibles en '{court.name}' el {booking_date}:")
    print(f"  {formatted_slots}")


def _create_booking_flow(service: BookingService) -> None:
    sports_complex = _select_complex(service)
    if sports_complex is None:
        return
    court = _select_court(service, sports_complex)
    if court is None:
        return

    booking_date = _prompt_text("Fecha (AAAA-MM-DD)", default=date.today().isoformat())
    slots = service.get_available_slots(court.id, booking_date)
    if not slots:
        print(f"\nLo sentimos, '{court.name}' no tiene espacios libres el {booking_date}.")
        return

    print("  Horas libres:", ", ".join(f"{hour:02d}:00" for hour in slots))
    start_hour = _prompt_int("Hora de inicio (formato 24h, ej. 18)")
    duration_hours = _prompt_int("Duración en horas", default=1)
    customer_name = _prompt_text("Tu nombre completo")
    customer_phone = _prompt_text("Tu teléfono de contacto", required=False)

    booking = service.create_booking(
        court_id=court.id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        booking_date=booking_date,
        start_hour=start_hour,
        duration_hours=duration_hours,
    )
    print("\nReserva confirmada con éxito:")
    print(f"  Código: {booking.id}")
    print(f"  Cancha: {court.name} ({sports_complex.name})")
    print(
        f"  Fecha y hora: {booking.date} de "
        f"{booking.start_hour:02d}:00 a {booking.end_hour:02d}:00"
    )
    print(f"  Total a pagar: ${booking.total_price:.2f}")


def _list_and_cancel_bookings(service: BookingService, allow_cancel: bool = True) -> None:
    date_filter = _prompt_text(
        "Filtrar por fecha AAAA-MM-DD (deja vacío para ver todas)",
        required=False,
    )
    bookings = service.list_bookings(booking_date=date_filter or None)
    if not bookings:
        print("\nNo se encontraron reservas con ese criterio.")
        return

    print("\n=== RESERVAS ===")
    for booking in bookings:
        court = service.get_court(booking.court_id)
        sports_complex = service.get_complex(court.complex_id)
        status_label = BOOKING_STATUS_LABELS[booking.status]
        print(
            f"  [{booking.id}] {booking.date} {booking.start_hour:02d}:00-{booking.end_hour:02d}:00 | "
            f"{sports_complex.name} / {court.name} | Cliente: {booking.customer_name} | "
            f"${booking.total_price:.2f} | Estado: {status_label}"
        )

    if allow_cancel:
        booking_code = _prompt_text(
            "\nSi deseas cancelar una reserva, escribe su código (Enter para volver)",
            required=False,
        )
        if booking_code:
            cancelled = service.cancel_booking(booking_code)
            print(f"  -> Reserva '{cancelled.id}' cancelada correctamente.")


def _register_complex_flow(service: BookingService) -> None:
    print("\n=== REGISTRAR COMPLEJO DEPORTIVO ===")
    name = _prompt_text("Nombre del complejo")
    address = _prompt_text("Dirección")
    owner_name = _prompt_text("Nombre del dueño / administrador")
    phone = _prompt_text("Teléfono del complejo", required=False)
    opening_hour = _prompt_int("Hora de apertura (0-23)", default=8)
    closing_hour = _prompt_int("Hora de cierre (1-24)", default=23)

    sports_complex = service.register_complex(
        name=name,
        address=address,
        owner_name=owner_name,
        opening_hour=opening_hour,
        closing_hour=closing_hour,
        phone=phone,
    )
    print(f"\nComplejo '{sports_complex.name}' registrado con ID: {sports_complex.id}")


def _add_court_flow(service: BookingService) -> None:
    print("\n=== AGREGAR CANCHA A UN COMPLEJO ===")
    sports_complex = _select_complex(service)
    if sports_complex is None:
        return

    name = _prompt_text("Nombre de la cancha (ej. Cancha 3 - Sintética)")
    court_type = _select_court_type()
    hourly_rate = _prompt_float("Precio por hora")
    indoor_answer = _prompt_text("¿Es techada? (s/n)", default="n").lower()
    is_indoor = indoor_answer in {"s", "si", "sí", "y", "yes"}

    court = service.add_court(
        complex_id=sports_complex.id,
        name=name,
        court_type=court_type,
        hourly_rate=hourly_rate,
        is_indoor=is_indoor,
    )
    print(f"\nCancha '{court.name}' agregada a '{sports_complex.name}' (ID: {court.id}).")


def _player_menu(service: BookingService) -> None:
    while True:
        print("\n--- MODO JUGADOR / CLIENTE ---")
        print("1. Ver complejos y canchas")
        print("2. Consultar disponibilidad de una cancha")
        print("3. Reservar una cancha")
        print("4. Ver / cancelar reservas")
        print("0. Volver al menú principal")

        choice = input("Elige una opción: ").strip()
        try:
            if choice == "1":
                _show_catalog(service)
            elif choice == "2":
                _check_availability(service)
            elif choice == "3":
                _create_booking_flow(service)
            elif choice == "4":
                _list_and_cancel_bookings(service, allow_cancel=True)
            elif choice == "0":
                return
            else:
                print("Opción no válida.")
        except ReservAppError as error:
            print(f"\n[Error] {error}")


def _owner_menu(service: BookingService) -> None:
    while True:
        print("\n--- MODO DUEÑO / ADMINISTRADOR ---")
        print("1. Registrar nuevo complejo deportivo")
        print("2. Agregar cancha a un complejo")
        print("3. Ver catálogo de complejos y canchas")
        print("4. Ver agenda de reservas / cancelar")
        print("0. Volver al menú principal")

        choice = input("Elige una opción: ").strip()
        try:
            if choice == "1":
                _register_complex_flow(service)
            elif choice == "2":
                _add_court_flow(service)
            elif choice == "3":
                _show_catalog(service)
            elif choice == "4":
                _list_and_cancel_bookings(service, allow_cancel=True)
            elif choice == "0":
                return
            else:
                print("Opción no válida.")
        except ReservAppError as error:
            print(f"\n[Error] {error}")


def main(data_path: Optional[Path] = None) -> None:
    """Application CLI entry point."""
    repository = JsonRepository(data_path or DEFAULT_DATA_PATH)
    service = BookingService(repository)

    if service.seed_sample_data():
        print("Se cargaron 2 complejos deportivos de ejemplo para que puedas empezar a probar.")

    print("==============================================")
    print("   RESERVAPP — GESTOR DE COMPLEJOS Y CANCHAS  ")
    print("==============================================")

    try:
        while True:
            print("\nSelecciona tu rol:")
            print("1. Jugador / Cliente (buscar y reservar canchas)")
            print("2. Dueño / Administrador (gestionar complejos y agenda)")
            print("0. Salir")

            choice = input("Elige una opción: ").strip()
            if choice == "1":
                _player_menu(service)
            elif choice == "2":
                _owner_menu(service)
            elif choice == "0":
                print("¡Hasta pronto!")
                break
            else:
                print("Opción no válida.")
    except (KeyboardInterrupt, EOFError):
        print("\nSesión finalizada.")
