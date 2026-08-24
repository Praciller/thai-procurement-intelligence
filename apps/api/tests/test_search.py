from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import ProcurementEmbedding, ProcurementRecord
from app.services.search import hybrid_candidates, search_records, tokenize


def _record(source_id: str, name: str, budget: str = "100") -> ProcurementRecord:
    return ProcurementRecord(
        source_name="fixture",
        dataset_type="synthetic",
        source_record_id=source_id,
        content_hash=(source_id * 64)[:64],
        project_name=name,
        agency_name="Fixture agency",
        budget_amount=Decimal(budget),
        is_synthetic=True,
    )


def test_thai_tokenization_preserves_subword_overlap():
    query = tokenize("คอมพิวเตอร์")
    matching = tokenize("ซื้อวัสดุคอมพิวเตอร์")
    unrelated = tokenize("ก่อสร้างถนน")

    assert query & matching
    assert len(query & matching) > len(query & unrelated)


def test_zero_budget_filter_is_not_treated_as_missing(session: Session):
    session.add_all([_record("zero", "Zero budget", "0"), _record("paid", "Paid budget", "100")])
    session.commit()

    results, total = search_records(session, {"max_budget": 0})

    assert total == 1
    assert [item.record.source_record_id for item in results] == ["zero"]


def test_hybrid_rank_fusion_is_not_dominated_by_keyword_score_magnitude(session: Session):
    query = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    keyword_heavy = _record("a", query)
    balanced = _record("b", "alpha")
    semantic_only = _record("c", "unrelated semantic candidate")
    session.add_all([keyword_heavy, balanced, semantic_only])
    session.flush()

    session.add_all(
        [
            ProcurementEmbedding(
                procurement_id=keyword_heavy.id,
                embedding_model="fixture",
                embedding=[0.0, 1.0],
                embedded_text=keyword_heavy.project_name,
                text_hash="a" * 64,
            ),
            ProcurementEmbedding(
                procurement_id=balanced.id,
                embedding_model="fixture",
                embedding=[1.0, 0.0],
                embedded_text=balanced.project_name,
                text_hash="b" * 64,
            ),
            ProcurementEmbedding(
                procurement_id=semantic_only.id,
                embedding_model="fixture",
                embedding=[0.8, 0.6],
                embedded_text=semantic_only.project_name,
                text_hash="c" * 64,
            ),
        ]
    )
    session.commit()

    results = hybrid_candidates(session, query, [1.0, 0.0], limit=2)

    assert [item.record.source_record_id for item in results] == ["b", "a"]
