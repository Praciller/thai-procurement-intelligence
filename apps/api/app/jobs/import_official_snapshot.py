from __future__ import annotations

import argparse
from pathlib import Path

from app.data_sources.egp_contract import EGPContractSnapshot
from app.database import SessionLocal
from app.services.ingestion import import_rows
from app.services.provenance import read_json, validate_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the approved DGA EGP snapshot.")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    metadata = read_json(args.metadata)
    validate_snapshot(args.file, metadata)
    source_rows = EGPContractSnapshot(args.file).rows()
    rows = (
        {
            **row,
            "source_url": metadata["source_url"],
            "source_snapshot_id": metadata["snapshot_id"],
            "source_retrieved_at": metadata["retrieved_at"],
            "source_updated_at": metadata.get("source_updated_at"),
            "source_license": metadata["license"],
            "source_checksum": metadata["sha256"],
            "mapping_version": metadata["mapping_version"],
        }
        for row in source_rows
    )
    with SessionLocal() as session:
        run, counters = import_rows(session, rows, EGPContractSnapshot.source_name, dataset_type="official_snapshot")
        print({"run_id": run.id, **counters.__dict__})


if __name__ == "__main__":
    main()
