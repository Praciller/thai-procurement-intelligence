import argparse
import asyncio

from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.models import ProcurementRecord
from app.routers.records import summarize_record


async def run(limit: int) -> None:
    init_db()
    with SessionLocal() as session:
        records = session.scalars(select(ProcurementRecord).limit(limit)).all()
        for record in records:
            await summarize_record(record.id, session=session)
    print({"summarized_records": len(records)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cached summaries for records")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(run(args.limit))


if __name__ == "__main__":
    main()

