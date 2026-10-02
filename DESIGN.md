# Technical Design Document: HR Resume Processing System

## 1. Overview

This document describes the architecture for a modular, Python-based backend system for HR resume screening and ranking. The system extracts text from PDF resumes, uses LLMs (via OpenRouter) to extract structured data and evaluate candidates against a rubric, and exposes a REST API for frontend consumption.

## 2. Architectural Principles

- **Modularity**: Each concern is isolated in its own module with clear interfaces
- **Separation of Concerns**: Data models, business logic, external integrations, and API layer are distinct
- **Testability**: Every module is independently testable with dependency injection
- **Configurability**: Environment-based configuration with sensible defaults
- **Extensibility**: Plugin architecture for parsers, LLM providers, and rubrics

## 3. Module Architecture

```
funnel/
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── settings.py         # Pydantic Settings (env vars, defaults)
│   └── constants.py        # Application constants
│
├── models/                 # Pure data structures (Pydantic models)
│   ├── __init__.py
│   ├── resume.py           # Resume, Candidate, Experience, Education, Skills
│   ├── job.py              # JobDescription, Requirements, Rubric
│   ├── evaluation.py       # EvaluationResult, Score, Ranking
│   └── api.py              # Request/Response DTOs
│
├── resume_parser/          # Text extraction from PDFs
│   ├── __init__.py
│   ├── base.py             # Abstract base class (ParserProtocol)
│   ├── pdfplumber_parser.py# pdfplumber implementation
│   ├── pymupdf_parser.py   # PyMuPDF implementation (fallback)
│   ├── factory.py          # Parser factory/selection logic
│   └── exceptions.py       # Parser-specific exceptions
│
├── llm_client/             # LLM integration (OpenRouter)
│   ├── __init__.py
│   ├── base.py             # Abstract base class (LLMClientProtocol)
│   ├── openrouter.py       # OpenRouter implementation
│   ├── prompts.py          # Prompt templates (jinja2)
│   ├── tools.py            # Tool/function calling definitions
│   ├── retry.py            # Retry logic with exponential backoff
│   └── exceptions.py       # LLM-specific exceptions
│
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── extraction.py       # Resume -> Structured data pipeline
│   ├── evaluation.py       # Rubric-based candidate evaluation
│   ├── ranking.py          # Ranking algorithms
│   ├── storage.py          # File-based persistence (JSON/JSONL)
│   └── pipeline.py         # End-to-end orchestration
│
├── api/                    # FastAPI request handling
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── resumes.py      # POST /resumes, GET /resumes, GET /resumes/{id}
│   │   ├── jobs.py         # POST /jobs, GET /jobs, GET /jobs/{id}
│   │   ├── evaluations.py  # POST /evaluations, GET /evaluations
│   │   └── rankings.py     # GET /rankings
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── middleware.py       # Logging, error handling, CORS
│   └── schemas.py          # API-specific schemas (if different from models)
│
├── main.py                 # Composition root, FastAPI app factory
├── cli.py                  # CLI commands for batch processing
│
├── tests/                  # Test suite (mirrors source structure)
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── conftest.py
│
├── data/                   # Runtime data (gitignored)
│   ├── resumes/            # Input PDFs
│   ├── processed/          # Extracted JSON
│   └── evaluations/        # Evaluation results
│
├── pyproject.toml          # Project config, dependencies, tool config
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
└── docker-compose.yml      # Optional: for local dev with services
```

## 4. Data Models (models/)

### 4.1 Resume Models
```python
# models/resume.py
class ContactInfo(BaseModel):
    email: EmailStr | None
    phone: str | None
    linkedin: HttpUrl | None
    github: HttpUrl | None
    location: str | None

class Experience(BaseModel):
    company: str
    title: str
    start_date: date
    end_date: date | None
    description: str
    technologies: list[str]

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str | None
    graduation_date: date | None
    gpa: float | None

class Skill(BaseModel):
    name: str
    category: SkillCategory  # TECHNICAL, SOFT, LANGUAGE, DOMAIN
    proficiency: ProficiencyLevel  # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    years_experience: float | None

class Resume(BaseModel):
    id: UUID
    raw_text: str
    file_path: Path
    file_hash: str  # SHA256 for deduplication
    candidate: Candidate
    extracted_at: datetime
    parser_used: str
```

### 4.2 Job & Rubric Models
```python
# models/job.py
class Requirement(BaseModel):
    id: str
    description: str
    weight: float  # 0-1, sums to 1 across requirements
    category: RequirementCategory  # MUST_HAVE, NICE_TO_HAVE, BONUS
    keywords: list[str]

class Rubric(BaseModel):
    id: UUID
    job_id: UUID
    name: str
    requirements: list[Requirement]
    scoring_method: ScoringMethod  # WEIGHTED_SUM, THRESHOLD, HYBRID
    passing_threshold: float  # 0-100
```

### 4.3 Evaluation Models
```python
# models/evaluation.py
class RequirementScore(BaseModel):
    requirement_id: str
    score: float  # 0-100
    evidence: list[str]  # Quotes from resume
    reasoning: str
    matched_keywords: list[str]

class EvaluationResult(BaseModel):
    id: UUID
    resume_id: UUID
    job_id: UUID
    rubric_id: UUID
    requirement_scores: list[RequirementScore]
    overall_score: float  # 0-100
    recommendation: Recommendation  # STRONG_HIRE, HIRE, MAYBE, NO_HIRE
    strengths: list[str]
    weaknesses: list[str]
    evaluated_at: datetime
    llm_model: str
    tokens_used: int
```

## 5. Resume Parser Module (resume_parser/)

### 5.1 Interface
```python
# resume_parser/base.py
class ParserProtocol(Protocol):
    def extract_text(self, file_path: Path) -> str: ...
    def extract_metadata(self, file_path: Path) -> dict: ...
    def supports(self, file_path: Path) -> bool: ...
```

### 5.2 Implementations
- **pdfplumber_parser**: Primary - better table/layout handling
- **pymupdf_parser**: Fallback - faster, better for scanned PDFs with OCR

### 5.3 Factory
```python
# resume_parser/factory.py
def get_parser(file_path: Path, prefer: str = "pdfplumber") -> ParserProtocol
```

## 6. LLM Client Module (llm_client/)

### 6.1 Interface
```python
# llm_client/base.py
class LLMClientProtocol(Protocol):
    async def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> LLMResponse: ...
    
    async def complete_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        **kwargs
    ) -> BaseModel: ...
```

### 6.2 OpenRouter Implementation
- Uses `openai` Python SDK with custom base_url
- Supports tool calling for structured extraction
- Implements retry with exponential backoff (tenacity)
- Rate limiting awareness
- Cost tracking per request

### 6.3 Prompts (Jinja2 Templates)
- `extract_resume.j2`: Extract structured data from raw text
- `evaluate_candidate.j2`: Score candidate against rubric
- `rank_candidates.j2`: Compare multiple candidates

## 7. Services Layer (services/)

### 7.1 Extraction Service
```python
# services/extraction.py
class ExtractionService:
    def __init__(self, parser: ParserProtocol, llm: LLMClientProtocol):
        self.parser = parser
        self.llm = llm
    
    async def extract(self, file_path: Path) -> Resume:
        # 1. Parse PDF -> raw text
        # 2. LLM structured extraction
        # 3. Validate & enrich
        # 4. Persist
```

### 7.2 Evaluation Service
```python
# services/evaluation.py
class EvaluationService:
    def __init__(self, llm: LLMClientProtocol, storage: Storage):
        self.llm = llm
        self.storage = storage
    
    async def evaluate(self, resume: Resume, rubric: Rubric) -> EvaluationResult:
        # 1. Build evaluation prompt with rubric
        # 2. Call LLM with structured output
        # 3. Validate scores
        # 4. Persist
```

### 7.3 Ranking Service
```python
# services/ranking.py
class RankingService:
    def rank(self, evaluations: list[EvaluationResult], method: RankingMethod) -> list[RankedCandidate]:
        # Methods: SCORE_DESC, WEIGHTED_COMPOSITE, PARETO_FRONTIER
```

### 7.4 Storage Service
```python
# services/storage.py
class Storage:
    def __init__(self, base_path: Path):
        self.resumes = JSONLStore(base_path / "resumes")
        self.jobs = JSONStore(base_path / "jobs")
        self.evaluations = JSONLStore(base_path / "evaluations")
```

## 8. API Layer (api/)

### 8.1 Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resumes/upload` | Upload PDF, returns Resume ID |
| GET | `/api/v1/resumes` | List resumes (pagination, filters) |
| GET | `/api/v1/resumes/{id}` | Get resume details |
| DELETE | `/api/v1/resumes/{id}` | Delete resume |
| POST | `/api/v1/jobs` | Create job with rubric |
| GET | `/api/v1/jobs` | List jobs |
| GET | `/api/v1/jobs/{id}` | Get job details |
| POST | `/api/v1/evaluations` | Evaluate resume against job |
| GET | `/api/v1/evaluations` | List evaluations |
| GET | `/api/v1/rankings?job_id=xxx` | Get ranked candidates for job |

### 8.2 Request/Response Examples

**POST /api/v1/resumes/upload**
```json
// Response 201
{
  "id": "uuid",
  "status": "processing",
  "message": "Resume uploaded, extraction started"
}
```

**GET /api/v1/resumes/{id}**
```json
{
  "id": "uuid",
  "candidate": {
    "name": "John Doe",
    "contact": {...},
    "summary": "Senior Python Developer...",
    "experience": [...],
    "education": [...],
    "skills": [...]
  },
  "extracted_at": "2024-01-15T10:30:00Z"
}
```

**POST /api/v1/evaluations**
```json
// Request
{
  "resume_id": "uuid",
  "job_id": "uuid",
  "rubric_id": "uuid"
}
// Response 201
{
  "id": "uuid",
  "overall_score": 87.5,
  "recommendation": "HIRE",
  "requirement_scores": [...]
}
```

## 9. Configuration (config/)

```python
# config/settings.py
class Settings(BaseSettings):
    # App
    APP_NAME: str = "Funnel HR"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Storage
    DATA_DIR: Path = Path("./data")
    RESUMES_DIR: Path = Path("./data/resumes")
    
    # LLM (OpenRouter)
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = "anthropic/claude-3.5-sonnet"
    EXTRACTION_MODEL: str = "anthropic/claude-3.5-sonnet"
    EVALUATION_MODEL: str = "anthropic/claude-3.5-sonnet"
    MAX_TOKENS: int = 8192
    TEMPERATURE: float = 0.1
    
    # Parser
    DEFAULT_PARSER: str = "pdfplumber"
    OCR_ENABLED: bool = False
    
    # Processing
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]
    BATCH_SIZE: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## 10. Rubric Design & Algorithm

### 10.1 Rubric Structure
Each job has a rubric with weighted requirements:
- **MUST_HAVE** (weight 0.6): Core qualifications, deal-breakers
- **NICE_TO_HAVE** (weight 0.3): Preferred qualifications
- **BONUS** (weight 0.1): Differentiators

### 10.2 Scoring Algorithm
```
For each requirement:
  1. LLM extracts evidence from resume
  2. LLM scores 0-100 based on evidence match
  3. Score weighted by requirement.weight

Overall = sum(req_score * req_weight) / sum(weights)
Normalized to 0-100 scale

Recommendation bands:
  90-100: STRONG_HIRE
  75-89:  HIRE
  60-74:  MAYBE
  0-59:   NO_HIRE
```

### 10.3 LLM Evaluation Prompt Strategy
- Few-shot examples for calibration
- Chain-of-thought reasoning required
- Evidence citations mandatory
- Structured output via tool calling

## 11. Error Handling & Resilience

- **Parser errors**: Log, skip file, continue batch
- **LLM errors**: Retry 3x with backoff, fallback model, circuit breaker
- **Validation errors**: Return 422 with details
- **Rate limits**: Queue with exponential backoff
- **Partial failures**: Transactional persistence (write-ahead log)

## 12. Testing Strategy

| Layer | Approach | Tools |
|-------|----------|-------|
| Unit | Mock all externals, test pure logic | pytest, pytest-mock |
| Integration | Testcontainers for API, real LLM calls (marked) | pytest, httpx |
| Contract | Schema validation for API | pydantic, schemathesis |
| E2E | Full pipeline with sample PDFs | pytest, playwright (later) |

## 13. Security Considerations

- API key never logged
- File upload validation (type, size, magic bytes)
- Path traversal prevention
- Rate limiting on API
- No PII in logs (hash emails/names)
- HTTPS in production (reverse proxy)

## 14. Deployment Considerations

- **Local**: `uvicorn main:app --reload`
- **Production**: Gunicorn + Uvicorn workers behind Nginx
- **Container**: Multi-stage Dockerfile
- **Scaling**: Stateless API, Redis for queue (future)
- **Monitoring**: Structured JSON logs, Prometheus metrics

## 15. Future Extensibility Points

- Plugin system for parsers (DOCX, TXT, HTML)
- Multiple LLM providers (Anthropic direct, Azure, local)
- Custom rubric types (coding challenge, take-home)
- Webhook notifications
- Batch async processing with Celery/RQ
- Vector search for semantic matching