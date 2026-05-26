import argparse

from app.database import SessionLocal, init_db
from app.services.ingestion import import_csv_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Import procurement CSV records")
    parser.add_argument("--file", required=True, help="CSV file path")
    parser.add_argument("--source", default="sample", help="Source name")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as session:
        run, counters = import_csv_file(session, args.file, source_name=args.source)
    print(
        {
            "run_id": run.id,
            "status": run.status,
            "total_rows": counters.total_rows,
            "inserted_rows": counters.inserted_rows,
            "updated_rows": counters.updated_rows,
            "failed_rows": counters.failed_rows,
        }
    )


if __name__ == "__main__":
    main()

