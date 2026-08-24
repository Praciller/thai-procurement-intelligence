from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import ProcurementEmbedding, ProcurementRecord
from app.services.search import hybrid_candidates, keyword_candidates, search_records, tokenize


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


def test_keyword_candidates_score_before_applying_result_limit(session: Session):
    session.add_all([_record(f"a-{index}", "alpha") for index in range(5)])
    session.add(_record("z-target", "alpha beta"))
    session.commit()

    results = keyword_candidates(session, "alpha beta", limit=1)

    assert [item.record.source_record_id for item in results] == ["z-target"]


def test_keyword_candidates_drop_weak_thai_ngram_collisions(session: Session):
    session.add(_record("weak", "\u0e42\u0e04\u0e23\u0e07\u0e01\u0e32\u0e23\u0e2a\u0e33\u0e23\u0e27\u0e08\u0e2d\u0e32\u0e04\u0e32\u0e23"))
    session.commit()

    results = keyword_candidates(session, "\u0e14\u0e32\u0e27\u0e40\u0e17\u0e35\u0e22\u0e21\u0e2a\u0e33\u0e23\u0e27\u0e08\u0e2d\u0e27\u0e01\u0e32\u0e28", limit=5)

    assert results == []


def test_keyword_candidates_reject_blank_query(session: Session):
    session.add(_record("row", "alpha"))
    session.commit()

    assert keyword_candidates(session, "   ", limit=5) == []


def test_exact_phrase_strictly_outranks_unordered_full_token_match(session: Session):
    session.add_all([_record("a-nonphrase", "beta alpha"), _record("z-phrase", "alpha beta")])
    session.commit()

    results = keyword_candidates(session, "alpha beta", limit=2)

    assert [item.record.source_record_id for item in results] == ["z-phrase", "a-nonphrase"]


def test_hybrid_candidates_reject_blank_query_before_semantic_retrieval(session: Session):
    record = _record("semantic", "unrelated")
    session.add(record)
    session.flush()
    session.add(
        ProcurementEmbedding(
            procurement_id=record.id,
            embedding_model="fixture",
            embedding=[1.0, 0.0],
            embedded_text=record.project_name,
            text_hash="d" * 64,
        )
    )
    session.commit()

    assert hybrid_candidates(session, "   ", [1.0, 0.0], limit=5) == []


def test_equal_keyword_scores_use_stable_source_key(session: Session):
    session.add_all([_record("b", "alpha"), _record("a", "alpha")])
    session.commit()

    results = keyword_candidates(session, "alpha", limit=2)

    assert [item.record.source_record_id for item in results] == ["a", "b"]


def test_min_budget_zero_is_not_treated_as_missing(session: Session):
    session.add_all([_record("zero", "Zero budget", "0"), _record("paid", "Paid budget", "100")])
    session.commit()

    results, total = search_records(session, {"min_budget": 0})

    assert total == 2
    assert {item.record.source_record_id for item in results} == {"zero", "paid"}
