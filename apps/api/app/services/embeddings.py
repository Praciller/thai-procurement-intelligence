from __future__ import annotations

import hashlib
import math
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProcurementEmbedding, ProcurementRecord
from app.services.normalization import text_hash
from app.services.search import tokenize


EMBEDDING_DIMENSIONS = 128
MOCK_EMBEDDING_MODEL = "hashing-token-v1"


def embedded_text(record: ProcurementRecord) -> str:
    return " | ".join(
        str(part)
        for part in (
            record.project_name,
            record.agency_name,
            record.province,
            record.procurement_method,
            record.procurement_category,
            record.budget_amount,
            record.announcement_date,
            record.raw_text or record.normalized_text,
        )
        if part
    )


def hash_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    counts: Counter[int] = Counter()
    for token in tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = -1 if digest[4] % 2 else 1
        counts[index] += sign
    vector = [float(counts.get(index, 0)) for index in range(dimensions)]
    magnitude = math.sqrt(sum(value * value for value in vector))
    if not magnitude:
        return vector
    return [value / magnitude for value in vector]


def ensure_embedding(session: Session, record: ProcurementRecord, model: str = MOCK_EMBEDDING_MODEL) -> ProcurementEmbedding:
    text = embedded_text(record)
    digest = text_hash(text)
    existing = session.scalar(
        select(ProcurementEmbedding).where(
            ProcurementEmbedding.procurement_id == record.id,
            ProcurementEmbedding.embedding_model == model,
        )
    )
    if existing and existing.text_hash == digest:
        return existing
    embedding = existing or ProcurementEmbedding(procurement_id=record.id, embedding_model=model, embedded_text=text, text_hash=digest)
    embedding.embedding = hash_embedding(text)
    embedding.embedded_text = text
    embedding.text_hash = digest
    session.add(embedding)
    session.commit()
    session.refresh(embedding)
    return embedding


def generate_missing_embeddings(session: Session, limit: int = 1000) -> int:
    records = session.scalars(select(ProcurementRecord).limit(limit)).all()
    count = 0
    for record in records:
        ensure_embedding(session, record)
        count += 1
    return count

