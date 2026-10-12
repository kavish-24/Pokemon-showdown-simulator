from collections.abc import Awaitable, Callable
from urllib.parse import urlparse

from src.agent.models import Action


class SafetyPolicy:
    def __init__(
        self,
        allowed_domains: list[str],
        confirm: Callable[[str], Awaitable[bool]] | None = None,
    ) -> None:
        self.allowed_domains = set(allowed_domains)
        self.confirm = confirm

    def validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in self.allowed_domains:
            raise ValueError("Navigation is outside the configured domain allowlist.")

    async def authorize(self, action: Action, description: str) -> None:
        if action.action in {"click_element", "click", "fill_secret", "fill", "type_into"}:
            if self.confirm is None or not await self.confirm(description):
                raise PermissionError("Action was not confirmed.")
