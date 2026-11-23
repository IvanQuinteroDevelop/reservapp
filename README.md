# ReservApp — Sports Complex & Court Booking Platform

A modular Python project designed to start simple (100% Python standard library) and scale cleanly into a full-featured, production-grade booking application for synthetic soccer fields and sports complexes.

## Project Structure

```text
reservapp/
├── pyproject.toml                   # Package metadata and optional future dependencies (dev, api)
├── run.py                           # Direct CLI launcher
├── data/                            # Local runtime JSON database (gitignored)
├── src/
│   └── reservapp/
│       ├── __init__.py
│       ├── __main__.py              # Supports `PYTHONPATH=src python -m reservapp`
│       ├── domain/
│       │   ├── models.py            # Core entities: SportsComplex, Court, Booking (dataclass + Enum)
│       │   └── exceptions.py        # Domain-specific business exceptions
│       ├── repositories/
│       │   ├── base.py              # Abstract repository contract (ABC)
│       │   └── json_repository.py   # In-memory (tests) and JSON file persistence
│       ├── services/
│       │   └── booking_service.py   # Business logic (operating hours, overlaps, pricing)
│       └── cli/
│           └── app.py               # Interactive CLI for Players and Complex Owners
└── tests/
    └── test_booking_service.py      # Unit tests using standard library `unittest`
```

### Architectural Principles
- **English-first codebase:** All filenames, modules, classes, variables, comments, tests, and documentation are written in English; only user-facing UI strings are localized in the presentation layer (`cli/`).
- **Layered architecture:** Separating `domain`, `repositories`, `services`, and `cli` enables migrating persistence (JSON -> SQLite -> PostgreSQL) or adding a REST API (FastAPI) without rewriting core business rules.

## Quickstart

From the project root directory:

1. **Activate the virtual environment** (recommended — enables the `python` command on macOS):
   ```bash
   source .venv/bin/activate
   python run.py
   ```
   *(You should see `(.venv)` at the start of your terminal prompt.)*

2. **Or run directly without activating `.venv`:**
   ```bash
   python3 run.py
   # or:
   ./run.py
   ```

3. **Run the unit test suite:**
   ```bash
   python3 -m unittest discover -s tests -v
   ```

## Evolution Roadmap

1. **Phase 1 (Current) — Core Python & Clean Architecture**
   - `dataclass`, `Enum`, type hints, custom exceptions, `pathlib`, `json`, `unittest`, and dual-role CLI (Player / Owner).
2. **Phase 2 — Real-World Business Rules**
   - User accounts with roles (`player`, `owner`, `admin`), dynamic pricing (peak/night rates), maintenance blocks, and cancellation policies.
3. **Phase 3 — Relational Database (SQLite -> PostgreSQL)**
   - Implement `SqliteRepository` via stdlib `sqlite3`, later evolving to **SQLAlchemy** + **Alembic** migrations.
4. **Phase 4 — Professional Developer Tooling**
   - Adopt `pytest`, `ruff` (linting & formatting), and `mypy` (static type checking).
5. **Phase 5 — REST API & Frontend**
   - Expose `BookingService` through **FastAPI** + **Pydantic** + JWT authentication.
6. **Phase 6 — Production Readiness**
   - Deposit/payment workflows, notifications, **Docker**, and CI with GitHub Actions.
