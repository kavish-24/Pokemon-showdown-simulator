from playwright.async_api import Page

from src.agent.models import Action
from src.agent.safety.policy import SafetyPolicy
from src.agent.safety.secrets import get_secret
from src.agent.browser.locators import resolve


async def execute(page: Page, action: Action, aliases: dict[str, list[str]], policy: SafetyPolicy) -> str:
    target: int | str | None = action.id if action.id is not None else action.selector
    if action.action == "finish":
        return action.message or "Completed."
    if target is None:
        raise ValueError("Action requires an id or selector.")
    locator = await resolve(page, target, aliases)
    if locator is None:
        raise ValueError("Target element was not found.")
    await policy.authorize(action, f"Allow {action.action} on {page.url}?")
    if action.action in {"click", "click_element"}:
        await locator.click()
    elif action.action == "fill_secret":
        if action.secret is None:
            raise ValueError("fill_secret requires a secret name.")
        await locator.fill(get_secret(action.secret))
    elif action.action in {"fill", "type_into"}:
        if action.value is None:
            raise ValueError("Action requires a value.")
        if action.action == "fill":
            await locator.fill(action.value)
        else:
            await locator.press_sequentially(action.value)
    elif action.action == "wait":
        await locator.wait_for(state="visible")
    return "action completed"
