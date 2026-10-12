from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SecretName = Literal["POKEMON_SHOWDOWN_USERNAME", "POKEMON_SHOWDOWN_PASSWORD"]
ActionName = Literal[
    "click_element", "fill_secret", "click", "fill", "type_into", "wait", "finish"
]


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: ActionName
    id: int | None = Field(default=None, ge=0)
    selector: str | None = None
    value: str | None = None
    secret: SecretName | None = None
    message: str | None = None


class Step(BaseModel):
    id: str
    goal: str
    hint: str
    allowed_actions: list[ActionName]
    done_when: str
    target: str | None = None
    secret: SecretName | None = None


class SOP(BaseModel):
    name: str
    max_attempts_per_step: int = Field(gt=0)
    steps: list[Step] = Field(min_length=1)


class RunState(BaseModel):
    task: str
    completed: list[str] = Field(default_factory=list)
    attempts: dict[str, int] = Field(default_factory=dict)
    history: list[dict[str, str]] = Field(default_factory=list)
    status: str = "running"


class Result(BaseModel):
    success: bool
    status: str
    message: str
