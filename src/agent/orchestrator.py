from pathlib import Path
import logging
from typing import Awaitable, Callable

from playwright.async_api import async_playwright

from src.agent.browser.executor import execute
from src.agent.browser.observer import snapshot
from src.agent.browser.session import BrowserSession
from src.agent.config import Settings
from src.agent.llm.base import LlmClient
from src.agent.llm.parsing import parse_action
from src.agent.llm.prompts import build_prompt
from src.agent.models import Action, Result, RunState
from src.agent.safety.policy import SafetyPolicy
from src.agent.sop.engine import SopEngine
from src.agent.state.store import StateStore

LOGGER = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, settings: Settings, llm: LlmClient, confirm: Callable[[str], Awaitable[bool]] | None = None) -> None:
        self.settings, self.llm = settings, llm
        self.confirm = confirm

    async def run(self, task: str, url: str) -> Result:
        from src.agent.sop.loader import load_selectors, load_sop
        state_store = StateStore(self.settings.state_file)
        state = state_store.start_new_run(state_store.load(task))
        engine = SopEngine(load_sop(self.settings.sop_file))
        aliases = load_selectors(self.settings.selectors_file)
        policy = SafetyPolicy(self.settings.allowed_domains, self.confirm)
        policy.validate_url(url)
        async with async_playwright() as playwright:
            async with BrowserSession(playwright, self.settings.browser_headless, self.settings.action_timeout_ms) as context:
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded")
                while True:
                    step = await engine.current_step(page, state)
                    state_store.save(state)
                    if step is None:
                        state.status = "completed"
                        state_store.save(state)
                        return Result(success=True, status="completed", message="SOP completed.")
                    if engine.attempts_exhausted(step, state):
                        state.status = "failed"
                        state_store.save(state)
                        return Result(
                            success=False,
                            status="step_attempt_limit",
                            message=f"Step {step.id} exceeded its attempt limit.",
                        )
                    attempt = engine.start_attempt(step, state)
                    try:
                        answer = await self.llm.predict(build_prompt(step, await snapshot(page), state))
                        LOGGER.info(
                            "LLM response received: step=%s length=%d preview=%r",
                            step.id,
                            len(answer),
                            answer[:500],
                        )
                        try:
                            action = parse_action(answer, fallback_secret=step.secret)
                        except ValueError:
                            # A credential-entry step has one deterministic, local action.
                            # Do not interpret arbitrary model prose as a browser command.
                            if step.secret and step.allowed_actions == ["fill_secret"]:
                                LOGGER.warning(
                                    "Using deterministic secret-fill fallback for step=%s; "
                                    "the model returned no parseable action.",
                                    step.id,
                                )
                                action = Action(action="fill_secret", secret=step.secret)
                            elif step.target and step.allowed_actions == ["click_element"]:
                                LOGGER.warning(
                                    "Using deterministic click fallback for step=%s; "
                                    "the model returned no parseable action.",
                                    step.id,
                                )
                                action = Action(action="click_element")
                            else:
                                raise
                        if action.action not in step.allowed_actions:
                            raise ValueError(f"Action {action.action} is not allowed for step {step.id}.")
                        previous_actions = [
                            item["action"]
                            for item in state.history
                            if item.get("step") == step.id
                            and item.get("outcome") == "action completed"
                        ]
                        if (
                            "fill_secret" in previous_actions
                            and action.action == "fill_secret"
                            and "click_element" in step.allowed_actions
                        ):
                            raise ValueError(
                                "The secret was already filled; click the visible submit control."
                            )
                        if (
                            step.secret
                            and action.action == "click_element"
                            and "fill_secret" not in previous_actions
                        ):
                            raise ValueError(
                                "Fill the configured secret before clicking the submit control."
                            )
                        if step.target:
                            action = action.model_copy(
                                update={
                                    "id": None,
                                    "selector": step.target,
                                    "secret": step.secret if action.action == "fill_secret" else action.secret,
                                }
                            )
                        outcome = await execute(page, action, aliases, policy)
                        state.history.append({"step": step.id, "action": action.action, "outcome": outcome})
                    except Exception as exc:
                        error_message = str(exc) or type(exc).__name__
                        LOGGER.error(
                            "Automation step failed: step=%s attempt=%d error=%s",
                            step.id,
                            attempt,
                            error_message,
                        )
                        state.history.append(
                            {
                                "step": step.id,
                                "action": "error",
                                "outcome": error_message[:240],
                            }
                        )
                        if attempt >= engine.sop.max_attempts_per_step:
                            state.status = "failed"
                            state_store.save(state)
                            return Result(
                                success=False,
                                status="step_failed",
                                message=f"Step {step.id} failed: {error_message}",
                            )
                    state_store.save(state)
