import pytest

from src.agent.models import RunState, SOP
from src.agent.sop.engine import SopEngine


class FakeLocator:
    def __init__(self, visible: bool = False) -> None:
        self.visible = visible

    async def count(self) -> int:
        return int(self.visible)

    async def is_visible(self) -> bool:
        return self.visible

    @property
    def first(self) -> "FakeLocator":
        return self


class FakePage:
    url = "https://play.pokemonshowdown.com/"

    def __init__(self, visible_selectors: set[str]) -> None:
        self.visible_selectors = visible_selectors

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(selector in self.visible_selectors)


@pytest.mark.asyncio
async def test_completed_step_is_reopened_when_dom_no_longer_matches() -> None:
    sop = SOP.model_validate(
        {
            "name": "test",
            "max_attempts_per_step": 2,
            "steps": [
                {
                    "id": "open",
                    "goal": "dialog",
                    "hint": "open",
                    "allowed_actions": ["click_element"],
                    "done_when": "visible:input[name=\"username\"]",
                }
            ],
        }
    )
    state = RunState(task="test", completed=["open"], attempts={"open": 2})
    step = await SopEngine(sop).current_step(FakePage(set()), state)
    assert step is not None
    assert state.completed == []
    assert state.attempts == {}
