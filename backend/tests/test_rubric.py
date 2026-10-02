"""Rubric aggregation is deterministic pure math."""
from funnel.rubric import aggregate


def test_aggregate_weighted_sum():
    scores = [
        {"criterion": "skills_match", "score_0_10": 10,
         "evidence": "e", "confidence": 1},
        {"criterion": "experience_relevance", "score_0_10": 5,
         "evidence": "", "confidence": 0.5},
        {"criterion": "education_fit", "score_0_10": 0,
         "evidence": "", "confidence": 0.5},
        {"criterion": "impact_signals", "score_0_10": 0,
         "evidence": "", "confidence": 0.5},
        {"criterion": "growth_trajectory", "score_0_10": 0,
         "evidence": "", "confidence": 0.5},
    ]
    total, breakdown = aggregate(scores)
    assert total == round((10 * 0.35 + 5 * 0.30) * 10, 1) == 50.0
    assert len(breakdown) == 5


def test_aggregate_clamps_and_ignores_unknown():
    total, breakdown = aggregate(
        [
            {"criterion": "skills_match", "score_0_10": 99},
            {"criterion": "nope", "score_0_10": 10},
        ]
    )
    assert total == 35.0  # 10 clamped * 0.35 * 10
    assert [b["criterion"] for b in breakdown] == ["skills_match"]
