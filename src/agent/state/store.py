from pathlib import Path

from src.agent.models import RunState


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, task: str) -> RunState:
        if not self.path.exists():
            return RunState(task=task)
        state = RunState.model_validate_json(self.path.read_text(encoding="utf-8"))
        if state.task != task:
            return RunState(task=task)
        if state.status == "failed":
            state.attempts = {}
            state.status = "running"
        return state

    def save(self, state: RunState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def start_new_run(state: RunState) -> RunState:
        state.completed = []
        state.attempts = {}
        state.status = "running"
        state.history.append(
            {"step": "__run__", "action": "start", "outcome": "login workflow started"}
        )
        return state
