from collections.abc import Awaitable, Callable
from urllib.parse import urlparse

from playwright.async_api import Page

Check = Callable[[Page, str], Awaitable[bool]]


async def visible(page: Page, argument: str) -> bool:
    locator = page.locator(argument).first
    return await locator.count() > 0 and await locator.is_visible()


async def gone(page: Page, argument: str) -> bool:
    return await page.locator(argument).count() == 0


async def url_contains(page: Page, argument: str) -> bool:
    return argument in page.url


async def text_present(page: Page, argument: str) -> bool:
    return argument in await page.locator("body").inner_text()


async def value_present(page: Page, argument: str) -> bool:
    locator = page.locator(argument).first
    return await locator.count() > 0 and bool(await locator.input_value())


CHECKS: dict[str, Check] = {
    "visible": visible,
    "gone": gone,
    "url_contains": url_contains,
    "text_present": text_present,
    "value_present": value_present,
}


async def run_check(page: Page, expression: str) -> bool:
    name, separator, argument = expression.partition(":")
    if not separator or name not in CHECKS:
        raise ValueError(f"Unsupported done_when check: {expression}")
    return await CHECKS[name](page, argument)
