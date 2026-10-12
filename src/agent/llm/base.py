from typing import Protocol


class LlmClient(Protocol):
    async def predict(self, prompt: str) -> str: ...
