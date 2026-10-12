"""Stateless asynchronous client for the decision-making API."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)
PREDICT_PATH = "/predict"


class LlmClientError(RuntimeError):
    """An inference request could not produce a valid answer."""


class LlmClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._retries = max(0, retries)
        self._client = httpx.AsyncClient(timeout=self._timeout, transport=transport)

    async def __aenter__(self) -> "LlmClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def predict(self, question: str) -> str:
        question = question.strip()
        if not question:
            raise LlmClientError("The inference question must not be empty.")

        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                # The API contract is exactly one top-level JSON field:
                # {"question": "<prompt>"}.
                request_body = {"question": question}
                response = await self._client.post(
                    f"{self._base_url}{PREDICT_PATH}",
                    json=request_body,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(payload.get("answer"), str):
                    raise LlmClientError("The inference response did not contain a string answer.")
                answer = payload["answer"].strip()
                if not answer:
                    raise LlmClientError("The inference response contained an empty answer.")
                return answer
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                if attempt < self._retries:
                    continue
                raise LlmClientError("The inference service could not be reached.") from exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                detail = "inference request was rejected" if status < 500 else "inference service failed"
                raise LlmClientError(f"{detail} (HTTP {status}).") from exc
            except (ValueError, json.JSONDecodeError) as exc:
                raise LlmClientError("The inference service returned invalid JSON.") from exc
            except LlmClientError:
                raise
            except httpx.HTTPError as exc:
                last_error = exc
                break
        LOGGER.error("Inference request failed: %s", type(last_error).__name__ if last_error else "unknown")
        raise LlmClientError("The inference request failed.") from last_error
