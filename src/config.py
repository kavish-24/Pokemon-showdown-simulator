"""Environment-driven server and runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from poke_env import ServerConfiguration


@dataclass(frozen=True)
class BotConfig:
    """Runtime settings loaded from environment variables."""

    server: ServerConfiguration
    data_dir: Path
    battles: int
    retry_limit: int
    backoff_seconds: float
    battle_timeout_seconds: float


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


def load_config() -> BotConfig:
    """Build all configuration in one place from environment variables."""
    ws_url = os.getenv("SHOWDOWN_WS_URL", "ws://localhost:8000/showdown/websocket")
    auth_url = os.getenv("SHOWDOWN_AUTH_URL", "http://localhost:8000")
    data_dir = Path(os.getenv("DATA_DIR", "./data"))
    return BotConfig(
        server=ServerConfiguration(
            websocket_url=ws_url,
            authentication_url=auth_url,
        ),
        data_dir=data_dir,
        battles=_env_int("PHASE0_BATTLES", 100),
        retry_limit=_env_int("PHASE0_RETRY_LIMIT", 5),
        backoff_seconds=_env_float("PHASE0_BACKOFF_SECONDS", 2.0),
        battle_timeout_seconds=_env_float("PHASE0_BATTLE_TIMEOUT_SECONDS", 180.0),
    )
