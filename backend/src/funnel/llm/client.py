"""OpenRouter (OpenAI-compatible) client + deterministic stub for tests.

Transport only: takes (system, user, json_schema), returns a parsed dict.
Validation against Pydantic models happens in services/, not here.
"""
from __future__ import annotations

import json
import time
from typing import Any, Protocol


class LlmClient(Protocol):
    def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> dict[str, Any]: ...


class StubLlmClient:
    """Deterministic canned response — for tests and offline ingest."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.calls: list[dict[str, str]] = []

    def complete_json(self, *, system: str, user: str, schema: dict) -> dict:
        self.calls.append({"system": system, "user": user})
        return json.loads(json.dumps(self._payload))


class OpenRouterClient:
    """Thin wrapper over the `openai` SDK pointed at OpenRouter.

    Swap to Azure/direct OpenAI by changing base_url + key + model only.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-4o-mini",
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._max_retries = max_retries

    def complete_json(self, *, system: str, user: str, schema: dict) -> dict:
        from openai import OpenAI

        client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = client.chat.completions.create(
                    model=self._model,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "funnel_result",
                            "strict": True,
                            "schema": schema,
                        },
                    },
                )
                content = resp.choices[0].message.content or "{}"
                return json.loads(content)
            except Exception as exc:  # retry then surface
                last_err = exc
                time.sleep(2**attempt)
        raise RuntimeError(f"LLM completion failed: {last_err}")
