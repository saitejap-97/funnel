"""Application settings using Pydantic Settings."""

from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from .constants import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    SUPPORTED_PARSERS,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "Funnel HR"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Storage paths
    DATA_DIR: Path = Field(default=Path("./data"))
    RESUMES_DIR: Path = Field(default=Path("./data/resumes"))
    PROCESSED_DIR: Path = Field(default=Path("./data/processed"))
    EVALUATIONS_DIR: Path = Field(default=Path("./data/evaluations"))
    JOBS_DIR: Path = Field(default=Path("./data/jobs"))
    
    # LLM (OpenRouter)
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = DEFAULT_MODEL
    EXTRACTION_MODEL: str = DEFAULT_MODEL
    EVALUATION_MODEL: str = DEFAULT_MODEL
    MAX_TOKENS: int = DEFAULT_MAX_TOKENS
    TEMPERATURE: float = DEFAULT_TEMPERATURE
    
    # Parser
    DEFAULT_PARSER: str = "pdfplumber"
    OCR_ENABLED: bool = False
    
    # File processing
    MAX_FILE_SIZE_MB: int = MAX_FILE_SIZE_BYTES // (1024 * 1024)
    ALLOWED_EXTENSIONS: list[str] = ALLOWED_EXTENSIONS
    
    # Processing
    BATCH_SIZE: int = 10
    REQUEST_TIMEOUT: int = 120
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Security
    SECRET_KEY: str = "dev-secret-change-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator("DATA_DIR", "RESUMES_DIR", "PROCESSED_DIR", "EVALUATIONS_DIR", "JOBS_DIR", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        """Expand user and resolve path."""
        if isinstance(v, str):
            v = Path(v).expanduser()
        return v.resolve()
    
    @field_validator("DEFAULT_PARSER")
    @classmethod
    def validate_parser(cls, v: str) -> str:
        """Validate parser is supported."""
        if v not in SUPPORTED_PARSERS:
            raise ValueError(f"Unsupported parser: {v}. Supported: {SUPPORTED_PARSERS}")
        return v
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, v: str | list[str]) -> list[str]:
        """Parse extensions from comma-separated string or list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        for dir_path in [self.DATA_DIR, self.RESUMES_DIR, self.PROCESSED_DIR, self.EVALUATIONS_DIR, self.JOBS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()