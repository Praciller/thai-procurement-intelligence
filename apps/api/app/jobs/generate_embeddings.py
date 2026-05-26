import argparse

from app.database import SessionLocal, init_db
from app.services.embeddings import generate_missing_embeddings


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic local embeddings")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    init_db()
    with SessionLocal() as session:
        count = generate_missing_embeddings(session, limit=args.limit)
    print({"embedded_records": count})


if __name__ == "__main__":
    main()

