"""Seed the API database with committed sample procurement records."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.jobs.import_csv import main


if __name__ == "__main__":
    main()
