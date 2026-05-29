import argparse

from sqlalchemy.orm import Session

from app.data_sources.open_api_importer import OpenApiDataSource
from app.database import SessionLocal
from app.models import IngestionRun
from app.services.ingestion import ImportCounters, import_rows


def import_source_url(session: Session, url: str, source_name: str = "open_api") -> tuple[IngestionRun, ImportCounters]:
    source = OpenApiDataSource(url=url, source_name=source_name)
    return import_rows(session, source.rows(), source.source_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import procurement rows from a JSON API source.")
    parser.add_argument("--url", required=True, help="JSON API URL returning a list or an object with an items array.")
    parser.add_argument("--source-name", default="open_api", help="Source name stored on imported records.")
    args = parser.parse_args()

    with SessionLocal() as session:
        run, counters = import_source_url(session, args.url, args.source_name)

    print(
        "Import completed: "
        f"run={run.id} status={run.status} inserted={counters.inserted_rows} "
        f"updated={counters.updated_rows} failed={counters.failed_rows}"
    )


if __name__ == "__main__":
    main()
