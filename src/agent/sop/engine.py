from src.agent.models import RunState, SOP, Step
from src.agent.sop.checks import run_check
from playwright.async_api import Page


class SopEngine:
    def __init__(self, sop: SOP) -> None:
        self.sop = sop

    async def current_step(self, page: Page, state: RunState) -> Step | None:
        for step in self.sop.steps:
            if step.id in state.completed:
                if await run_check(page, step.done_when):
                    continue
                state.completed.remove(step.id)
                state.attempts.pop(step.id, None)
            if await run_check(page, step.done_when):
                state.completed.append(step.id)
                continue
            return step
        return None

    def start_attempt(self, step: Step, state: RunState) -> int:
        state.attempts[step.id] = state.attempts.get(step.id, 0) + 1
        return state.attempts[step.id]

    def attempts_exhausted(self, step: Step, state: RunState) -> bool:
        return state.attempts.get(step.id, 0) > self.sop.max_attempts_per_step
