from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    api_base_url: str = "https://2f61-146-148-48-224.ngrok-free.app"
    api_timeout_seconds: float = Field(default=30, gt=0)
    api_retries: int = Field(default=2, ge=0)
    browser_headless: bool = True
    action_timeout_ms: float = Field(default=10_000, gt=0)
    state_file: Path = Path(".agent/run-state.json")
    selectors_file: Path = Path("config/selectors.yaml")
    sop_file: Path = Path("config/sops/login.yaml")
    allowed_domains: list[str] = ["play.pokemonshowdown.com"]

    @classmethod
    def from_env(cls, root: Path) -> "Settings":
        load_dotenv(root / ".env", override=False)
        return cls(
            api_base_url=os.getenv("LLM_API_BASE_URL", cls.model_fields["api_base_url"].default),
            api_timeout_seconds=float(os.getenv("LLM_API_TIMEOUT_SECONDS", "30")),
            api_retries=int(os.getenv("LLM_API_RETRIES", "2")),
            state_file=root / os.getenv("AGENT_STATE_FILE", ".agent/run-state.json"),
            selectors_file=root / os.getenv("AGENT_SELECTORS_FILE", "config/selectors.yaml"),
            sop_file=root / os.getenv("AGENT_SOP_FILE", "config/sops/login.yaml"),
            browser_headless=os.getenv("BROWSER_HEADLESS", "true").lower() not in {"0", "false", "no"},
        )
