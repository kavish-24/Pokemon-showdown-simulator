from playwright.async_api import Locator, Page
from rapidfuzz import fuzz


async def resolve(page: Page, target: int | str, aliases: dict[str, list[str]]) -> Locator | None:
    if isinstance(target, int):
        locator = page.locator(f'[data-agent-id="{target}"]').first
        if await locator.count() and await locator.is_visible():
            return locator
        return None
    candidates = aliases.get(target, [target])
    for candidate in candidates:
        try:
            locator = (
                page.get_by_text(candidate.removeprefix("text="), exact=True)
                if candidate.startswith("text=")
                else page.locator(candidate)
            )
            for item in await locator.all():
                if await item.is_visible() and await item.is_enabled():
                    return item
        except Exception:
            continue
    elements = await page.locator("button,input,textarea,select").all()
    best: tuple[float, Locator] | None = None
    for locator in elements:
        if not await locator.is_visible() or not await locator.is_enabled():
            continue
        label = await locator.get_attribute("name") or await locator.get_attribute("placeholder") or await locator.inner_text()
        score = fuzz.token_set_ratio(target.lower(), label.lower())
        if score >= 60 and (best is None or score > best[0]):
            best = (score, locator)
    return best[1] if best else None
