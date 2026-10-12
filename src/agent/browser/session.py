from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Playwright


class BrowserSession:
    def __init__(self, playwright: Playwright, headless: bool, timeout_ms: float) -> None:
        self.playwright = playwright
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def __aenter__(self) -> BrowserContext:
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.context.set_default_timeout(self.timeout_ms)
        return self.context

    async def __aexit__(self, *_args: object) -> None:
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
