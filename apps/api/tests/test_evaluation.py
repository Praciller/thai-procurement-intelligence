import math

import pytest

from app.jobs import evaluate_official_snapshot as evaluation


def test_score_ranking_reports_precision_recall_ndcg_and_mrr():
    score_ranking = getattr(evaluation, "score_ranking")

    metrics = score_ranking(["irrelevant", "relevant-b", "relevant-a"], {"relevant-a", "relevant-b"}, k=3)

    expected_dcg = 1 / math.log2(3) + 1 / math.log2(4)
    ideal_dcg = 1 + 1 / math.log2(3)
    assert metrics["precision_at_k"] == pytest.approx(2 / 3)
    assert metrics["recall_at_k"] == 1.0
    assert metrics["ndcg_at_k"] == pytest.approx(expected_dcg / ideal_dcg)
    assert metrics["mrr"] == 0.5
    assert metrics["eligible_for_relevance_average"] is True


def test_score_ranking_keeps_negative_queries_out_of_relevance_averages():
    score_ranking = getattr(evaluation, "score_ranking")

    metrics = score_ranking(["false-positive"], set(), k=5)

    assert metrics["eligible_for_relevance_average"] is False
    assert metrics["false_positive_count"] == 1
    assert metrics["precision_at_k"] is None
    assert metrics["recall_at_k"] is None
    assert metrics["ndcg_at_k"] is None
    assert metrics["mrr"] is None


def test_judgment_validation_rejects_unknown_snapshot_ids():
    validate_judgments = getattr(evaluation, "validate_judgments")
    judgments = {
        "snapshot_id": "fixture",
        "queries": [
            {
                "id": "known-and-unknown",
                "query": "fixture",
                "relevant_source_record_ids": ["known", "missing"],
            }
        ],
    }

    with pytest.raises(ValueError, match="missing"):
        validate_judgments(judgments, {"known"})
