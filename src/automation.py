"""Safe observe -> decide -> act browser automation workflow."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

from playwright.async_api import Browser, Error as PlaywrightError, Locator, Page, async_playwright
from rapidfuzz import fuzz

from src.llm_client import LlmClient, LlmClientError

LOGGER = logging.getLogger(__name__)
ALLOWED_ACTIONS = {
    "navigate",
    "click",
    "click_element",
    "fill",
    "fill_secret",
    "type",
    "type_into",
    "wait",
    "extract",
    "finish",
}
CONSEQUENTIAL_ACTIONS = {
    "click",
    "click_element",
    "fill",
    "fill_secret",
    "type",
    "type_into",
}


@dataclass(frozen=True)
class AutomationConfig:
    llm_base_url: str = "https://c2e2-34-132-39-236.ngrok-free.app"
    llm_timeout_seconds: float = 30.0
    llm_retries: int = 2
    max_steps: int = 8
    headless: bool = True
    action_timeout_ms: float = 10_000
    selectors_path: Path = Path("selectors.json")

    @classmethod
    def from_environment(cls, *, headless: bool = True, max_steps: int = 8) -> "AutomationConfig":
        default_selectors_path = Path(__file__).resolve().parent.parent / "selectors.json"
        return cls(
            llm_base_url=os.getenv(
                "LLM_API_BASE_URL",
                "https://c2e2-34-132-39-236.ngrok-free.app",
            ),
            llm_timeout_seconds=float(os.getenv("LLM_API_TIMEOUT_SECONDS", "30")),
            llm_retries=int(os.getenv("LLM_API_RETRIES", "2")),
            max_steps=max(1, max_steps),
            headless=headless,
            selectors_path=Path(os.getenv("AUTOMATION_SELECTORS_FILE", str(default_selectors_path))),
        )


@dataclass(frozen=True)
class AutomationResult:
    success: bool
    status: str
    message: str


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _element_id(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _answer_payload(answer: str) -> dict[str, Any] | None:
    candidate = answer.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
    decoder = json.JSONDecoder()
    for index, character in enumerate(candidate):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(candidate[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _answer_action(answer: str) -> dict[str, Any] | None:
    payload = _answer_payload(answer)
    if payload is not None:
        return payload
    command = answer.strip().strip("`").strip()
    click_match = re.search(r"\bclick(?:_element)?\s*\(\s*(\d+)\s*\)", command, re.IGNORECASE)
    if click_match:
        return {"action": "click_element", "id": int(click_match.group(1))}
    type_match = re.search(
        r"\b(?:type|type_into)\s*\(\s*(\d+)\s*,\s*(['\"])(.*?)\2\s*\)",
        command,
        re.IGNORECASE | re.DOTALL,
    )
    if type_match:
        return {
            "action": "type_into",
            "id": int(type_match.group(1)),
            "value": type_match.group(3),
        }
    return None


class AutomationWorkflow:
    def __init__(
        self,
        llm: LlmClient,
        config: AutomationConfig,
        confirm_action: Callable[[str], Awaitable[bool]] | None = None,
    ) -> None:
        self._llm = llm
        self._config = config
        self._confirm_action = confirm_action
        self._selectors = self._load_selectors(config.selectors_path)

    @staticmethod
    def _load_selectors(path: Path) -> dict[str, list[str]]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            LOGGER.warning("Selector file not found: %s", path)
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.error("Could not load selector file %s: %s", path, type(exc).__name__)
            return {}
        if not isinstance(payload, dict):
            LOGGER.error("Selector file must contain a JSON object: %s", path)
            return {}
        return {
            name: values
            for name, values in payload.items()
            if isinstance(name, str)
            and isinstance(values, list)
            and all(isinstance(selector, str) and selector.strip() for selector in values)
        }

    async def run(self, task: str, initial_url: str | None = None) -> AutomationResult:
        if not task.strip():
            return AutomationResult(False, "invalid_input", "The automation task must not be empty.")
        if initial_url and not _valid_url(initial_url):
            return AutomationResult(False, "invalid_input", "The initial URL must use HTTP or HTTPS.")

        async with async_playwright() as playwright:
            browser: Browser | None = None
            try:
                browser = await playwright.chromium.launch(headless=self._config.headless)
                page = await browser.new_page()
                page.set_default_timeout(self._config.action_timeout_ms)
                if initial_url:
                    await page.goto(initial_url, wait_until="domcontentloaded")
                return await self._loop(page, task)
            except Exception as exc:
                LOGGER.exception("Browser automation failed: %s", type(exc).__name__)
                return AutomationResult(False, "error", "Browser automation failed.")
            finally:
                if browser:
                    await browser.close()

    async def _loop(self, page: Page, task: str) -> AutomationResult:
        correction = ""
        for step in range(self._config.max_steps):
            context = await self._observe(page)
            question = (
                "You are an action planner. Return ONLY one JSON object, with no explanation, "
                "markdown, or planning text. If JSON is impossible, use exactly click(id) or "
                "type(id, \"value\") on one line. "
                "Return exactly one JSON object with action and action-specific fields. "
                "Choose the next appropriate action from the current page context; do not "
                "follow a hardcoded sequence. You may wait for a known selector before using it. "
                "Prefer numeric element IDs from interactive_elements: "
                "click_element(id), type_into(id, value), or fill_secret(id, secret). "
                "You may also use a selector key or visible-text query when no ID is suitable. "
                "Allowed actions: navigate(url), click(selector), click_element(id), "
                "fill(selector, value), "
                "fill_secret(selector, secret), "
                "type(selector, value), type_into(id, value), wait(selector), "
                "extract(selector), finish(message). "
                "Use only selectors present in the page context. Never return code. "
                "You may use a selector key from known_selectors, or a semantic selector "
                "such as text=Choose username. Do not add backslashes before selector quotes. "
                "For fill_secret, secret must be one of "
                "POKEMON_SHOWDOWN_USERNAME or POKEMON_SHOWDOWN_PASSWORD. "
                "Secret values are never included in page context or sent to the API. "
                "Task: " + task + "\nPage context: " + json.dumps(context, ensure_ascii=True)
                + correction
            )
            try:
                answer = await self._llm.predict(question)
            except LlmClientError as exc:
                return AutomationResult(False, "llm_error", str(exc))
            action = _answer_action(answer)
            if action is None:
                correction = (
                    "\nYour previous response was not executable JSON. "
                    "Do not describe what you plan to do. Respond with one action now, "
                    'for example {"action":"wait","selector":"login_username"} or click(7).'
                )
                LOGGER.warning("Model returned non-action response at step %s; retrying", step + 1)
                continue
            if not isinstance(action.get("action"), str):
                return AutomationResult(
                    False,
                    "invalid_model_action",
                    "The model returned JSON without a valid action field.",
                )
            result = await self._execute(page, action)
            if result:
                return result
            LOGGER.info("Completed automation step %s", step + 1)
        return AutomationResult(False, "step_limit", "The automation step limit was reached.")

    async def _observe(self, page: Page) -> dict[str, str]:
        return {
            "url": page.url,
            "title": await page.title(),
            "text": (await page.locator("body").inner_text())[:8_000],
            "known_selectors": json.dumps(self._selectors, ensure_ascii=True),
            "interactive_elements": json.dumps(await self._collect_interactive(page), ensure_ascii=True),
        }

    async def _collect_interactive(self, page: Page) -> list[dict[str, Any]]:
        return await page.evaluate(
            """() => {
                const selector =
                    'a, button, input, textarea, select, [role="button"], [role="link"], [onclick], [tabindex]';
                return [...document.querySelectorAll(selector)].map((element, id) => {
                    const rect = element.getBoundingClientRect();
                    const style = getComputedStyle(element);
                    const visible = rect.width > 0 && rect.height > 0 &&
                        style.visibility !== 'hidden' && style.display !== 'none';
                    element.setAttribute('data-agent-id', String(id));
                    return {
                        id,
                        tag: element.tagName.toLowerCase(),
                        type: element.getAttribute('type') || '',
                        text: (element.innerText || element.value || '').trim().slice(0, 80),
                        aria: element.getAttribute('aria-label') || '',
                        placeholder: element.getAttribute('placeholder') || '',
                        name: element.getAttribute('name') || '',
                        title: element.getAttribute('title') || '',
                        visible
                    };
                }).filter(element => element.visible);
            }"""
        )

    async def _locator_by_id(self, page: Page, value: Any) -> Locator | None:
        element_id = _element_id(value)
        if element_id is None:
            return None
        locator = page.locator(f'[data-agent-id="{element_id}"]').first
        return locator if await locator.count() else None

    async def _find_locator(
        self,
        page: Page,
        selector: str,
        *,
        require_present: bool = True,
        element_id: Any = None,
    ) -> Locator | None:
        if element_id is not None:
            return await self._locator_by_id(page, element_id)
        # Some models preserve JSON escaping in selector strings. Normalize it
        # before handing the value to Playwright.
        normalized_selector = selector.replace('\\"', '"').replace("\\'", "'")
        candidates = self._selectors.get(normalized_selector, [normalized_selector])
        for candidate in candidates:
            try:
                locator = page.locator(candidate).first
                if not require_present or await locator.count() > 0:
                    return locator
            except PlaywrightError:
                LOGGER.warning("Ignoring invalid selector candidate: %s", candidate)
        # Let the model use Playwright's semantic text locator without needing
        # to construct CSS :has-text syntax.
        if normalized_selector.startswith("text="):
            text = normalized_selector[5:].strip()
            if text:
                locator = page.get_by_text(text, exact=True).first
                if not require_present or await locator.count() > 0:
                    return locator
        elements = await self._collect_interactive(page)
        query = normalized_selector.removeprefix("text=").strip().lower()
        scored = []
        for element in elements:
            haystack = " ".join(
                str(element.get(field, ""))
                for field in ("text", "aria", "placeholder", "name", "title")
            ).strip()
            if haystack:
                score = max(
                    fuzz.partial_ratio(query, haystack.lower()),
                    fuzz.token_set_ratio(query, haystack.lower()),
                )
                scored.append((score, element["id"]))
        if scored:
            score, best_id = max(scored)
            if score >= 60:
                return await self._locator_by_id(page, best_id)
        return None

    async def _execute(self, page: Page, action: dict[str, Any]) -> AutomationResult | None:
        name = action["action"]
        if name not in ALLOWED_ACTIONS:
            return AutomationResult(False, "invalid_model_action", f"Unsupported action: {name}.")
        if name == "finish":
            message = action.get("message")
            return AutomationResult(True, "completed", message if isinstance(message, str) else "Completed.")
        if name == "navigate":
            url = action.get("url")
            if not isinstance(url, str) or not _valid_url(url):
                return AutomationResult(False, "invalid_action", "Navigation requires a valid HTTP(S) URL.")
            await page.goto(url, wait_until="domcontentloaded")
            return None

        element_id = action.get("id") if name in {"click_element", "type_into", "fill_secret"} else None
        if name in {"click_element", "type_into", "fill_secret"} and element_id is None:
            return AutomationResult(False, "invalid_action", f"{name} requires a numeric element id.")
        selector = action.get("selector")
        if element_id is None and (not isinstance(selector, str) or not selector.strip()):
            return AutomationResult(False, "invalid_action", f"{name} requires a selector.")
        locator = await self._find_locator(
            page,
            selector.strip() if isinstance(selector, str) else "",
            require_present=name != "wait",
            element_id=element_id,
        )
        if locator is None:
            return AutomationResult(False, "invalid_action", "The requested element was not found.")
        if name in CONSEQUENTIAL_ACTIONS:
            LOGGER.warning("Consequential action requested: %s", name)
            if self._confirm_action is None or not await self._confirm_action(
                f"Allow {name} on {page.url} using selector {selector!r}?"
            ):
                return AutomationResult(False, "confirmation_required", f"Confirmation required before {name}.")
            try:
                if name in {"click", "click_element"}:
                    await locator.click()
                elif name == "fill_secret":
                    secret_name = action.get("secret")
                    secret_value = os.getenv(secret_name) if isinstance(secret_name, str) else None
                    if secret_name not in {
                        "POKEMON_SHOWDOWN_USERNAME",
                        "POKEMON_SHOWDOWN_PASSWORD",
                    }:
                        return AutomationResult(False, "invalid_action", "Unknown secret name.")
                    if not secret_value:
                        return AutomationResult(
                            False,
                            "missing_configuration",
                            f"{secret_name} is not configured.",
                        )
                    await locator.fill(secret_value)
                else:
                    value = action.get("value")
                    if not isinstance(value, str):
                        return AutomationResult(False, "invalid_action", f"{name} requires a string value.")
                    if name in {"fill", "fill_secret"}:
                        await locator.fill(value)
                    else:
                        await locator.press_sequentially(value)
            except PlaywrightError:
                LOGGER.warning("Playwright could not execute %s for selector %r", name, selector)
                return AutomationResult(False, "invalid_action", f"Could not execute {name} for the selector.")
            return None
        try:
            if name == "wait":
                await locator.wait_for(state="visible")
            elif name == "extract":
                text = await locator.inner_text()
                return AutomationResult(True, "extracted", text)
        except PlaywrightError:
            LOGGER.warning("Playwright could not execute %s for selector %r", name, selector)
            return AutomationResult(False, "invalid_action", f"Could not execute {name} for the selector.")
        return None
