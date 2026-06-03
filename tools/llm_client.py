#!/usr/bin/env python3
"""Small OpenRouter client for autograding helpers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


class LlmClientError(Exception):
    """Raised when an LLM provider request fails."""


class OpenRouterClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise LlmClientError("OPENROUTER_API_KEY is required.")

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any] | None = None,
        temperature: float = 0,
        max_tokens: int = 2000,
        seed: int | None = None,
        reasoning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            body["seed"] = seed
        if reasoning:
            body["reasoning"] = reasoning
        if response_schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "autograde_result",
                    "strict": True,
                    "schema": response_schema,
                },
            }

        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
        )
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header("X-Title", "advanced-cryptography-2026-autograde")

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LlmClientError(f"OpenRouter request failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise LlmClientError(f"OpenRouter request failed: {exc}") from exc

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise LlmClientError("OpenRouter returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise LlmClientError("OpenRouter returned a non-object response.")
        return data
