import asyncio

import httpx
import pytest

from src.llm_client import LlmClient, LlmClientError


def test_predict_sends_question_and_returns_answer():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"answer": "ok"})

    transport = httpx.MockTransport(handler)

    async def run() -> str:
        async with LlmClient("https://api.example", transport=transport) as client:
            return await client.predict("What is 2 + 2?")

    assert asyncio.run(run()) == "ok"

    assert requests[0].url.path == "/predict"
    assert requests[0].read() == b'{"question":"What is 2 + 2?"}'


def test_predict_rejects_missing_answer():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": "not-answer"})

    async def run() -> None:
        async with LlmClient("https://api.example", transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(LlmClientError, match="string answer"):
                await client.predict("task")

    asyncio.run(run())


def test_predict_reports_http_errors():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"})

    async def run() -> None:
        async with LlmClient("https://api.example", transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(LlmClientError, match="HTTP 400"):
                await client.predict("task")

    asyncio.run(run())
