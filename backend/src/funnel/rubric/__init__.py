"""Versioned rubric: criteria + prompt builders + deterministic aggregation.

Only module allowed to contain prompt text. No I/O.
"""
from funnel.rubric.default_rubric import (
    DEFAULT_CRITERIA,
    RUBRIC_VERSION,
    aggregate,
    build_profile_prompt,
    build_rank_prompt,
    profile_json_schema,
    rank_json_schema,
)

__all__ = [
    "DEFAULT_CRITERIA",
    "RUBRIC_VERSION",
    "aggregate",
    "build_profile_prompt",
    "build_rank_prompt",
    "profile_json_schema",
    "rank_json_schema",
]
