#!/usr/bin/env python3
"""Direct launcher to run the application without installing external packages.

Usage:
    ./run.py
    python3 run.py
    source .venv/bin/activate && python run.py
"""

from pathlib import Path
import sys

# Add `src/` to Python's module search path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from reservapp.cli.app import main  # noqa: E402


if __name__ == "__main__":
    main()
