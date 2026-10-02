"""Models: validation edge cases."""
import pytest
from pydantic import ValidationError

from funnel.models.profile import CandidateProfile
from funnel.models.ranking import RankResult


def test_profile_defaults():
    p = CandidateProfile(id="abc", source_file="x.pdf", file_hash="h")
    assert p.skills == [] and p.profile_status.value == "ok"


def test_rank_result_rejects_out_of_range():
    with pytest.raises(ValidationError):
        RankResult(
            candidate_id="x",
            total_100=101,
            breakdown=[],
            rationale="",
        )
    with pytest.raises(ValidationError):
        RankResult(
            candidate_id="x",
            total_100=50,
            breakdown=[
                {
                    "criterion": "skills_match",
                    "score_0_10": 11,
                    "weight": 0.35,
                    "evidence": "",
                    "confidence": 0.5,
                }
            ],
            rationale="",
        )
