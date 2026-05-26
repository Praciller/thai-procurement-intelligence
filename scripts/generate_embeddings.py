"""Generate local deterministic embeddings through the API job module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.jobs.generate_embeddings import main


if __name__ == "__main__":
    main()
