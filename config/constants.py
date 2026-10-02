"""Application constants and enumerations."""

from enum import Enum


class SkillCategory(str, Enum):
    """Categories for skills."""
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    DOMAIN = "domain"
    TOOL = "tool"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    OTHER = "other"


class ProficiencyLevel(str, Enum):
    """Proficiency levels for skills."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class RequirementCategory(str, Enum):
    """Categories for job requirements."""
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    BONUS = "bonus"


class ScoringMethod(str, Enum):
    """Methods for calculating overall scores."""
    WEIGHTED_SUM = "weighted_sum"
    THRESHOLD = "threshold"
    HYBRID = "hybrid"


class Recommendation(str, Enum):
    """Hiring recommendations based on evaluation."""
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    MAYBE = "maybe"
    NO_HIRE = "no_hire"


class RankingMethod(str, Enum):
    """Methods for ranking candidates."""
    SCORE_DESC = "score_desc"
    WEIGHTED_COMPOSITE = "weighted_composite"
    PARETO_FRONTIER = "pareto_frontier"


# Recommendation thresholds
RECOMMENDATION_THRESHOLDS = {
    Recommendation.STRONG_HIRE: 90,
    Recommendation.HIRE: 75,
    Recommendation.MAYBE: 60,
    Recommendation.NO_HIRE: 0,
}

# Default requirement weights by category
DEFAULT_CATEGORY_WEIGHTS = {
    RequirementCategory.MUST_HAVE: 0.6,
    RequirementCategory.NICE_TO_HAVE: 0.3,
    RequirementCategory.BONUS: 0.1,
}

# File processing
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf"}
SUPPORTED_PARSERS = ["pdfplumber", "pymupdf"]

# LLM defaults
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 8192
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"