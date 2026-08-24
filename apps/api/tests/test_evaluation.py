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


def test_summarize_judged_metrics_averages_positive_queries_and_counts_negative_false_positives():
    summarize = getattr(evaluation, "summarize_judged_metrics")
    metrics = [
        {"precision_at_k": 1.0, "recall_at_k": 0.5, "ndcg_at_k": 0.75, "mrr": 1.0, "false_positive_count": 0, "eligible_for_relevance_average": True},
        {"precision_at_k": 0.5, "recall_at_k": 1.0, "ndcg_at_k": 0.5, "mrr": 0.5, "false_positive_count": 1, "eligible_for_relevance_average": True},
        {"precision_at_k": None, "recall_at_k": None, "ndcg_at_k": None, "mrr": None, "false_positive_count": 3, "eligible_for_relevance_average": False},
    ]

    summary = summarize(metrics, k=5)

    assert summary["positive_query_count"] == 2
    assert summary["negative_query_count"] == 1
    assert summary["mean_precision_at_5"] == pytest.approx(0.75)
    assert summary["mean_recall_at_5"] == pytest.approx(0.75)
    assert summary["mean_ndcg_at_5"] == pytest.approx(0.625)
    assert summary["mean_mrr"] == pytest.approx(0.75)
    assert summary["negative_false_positive_count"] == 3

def test_console_json_is_ascii_safe_for_windows_code_pages():
    console_json = getattr(evaluation, "console_json")
    payload = {"query": "\u0e04\u0e2d\u0e21\u0e1e\u0e34\u0e27\u0e40\u0e15\u0e2d\u0e23\u0e4c"}

    encoded = console_json(payload).encode("cp1252")

    assert b"\\u0e" in encoded
