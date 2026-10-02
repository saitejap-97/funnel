"""LLM transport: auth + structured completion. No rubric text, no ranking math."""
from funnel.llm.client import LlmClient, OpenRouterClient, StubLlmClient

__all__ = ["LlmClient", "OpenRouterClient", "StubLlmClient"]
