"""Phase 0 unattended random player."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from poke_env.player import RandomPlayer

from src.config import BotConfig, load_config
from src.db.init_db import initialize_database

LOGGER = logging.getLogger(__name__)


def _load_progress(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"completed_battle_ids": [], "completed_count": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_progress(path: Path, progress: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(progress, indent=2), encoding="utf-8")
    temporary.replace(path)


def _battle_ids(player: RandomPlayer) -> list[str]:
    battles = getattr(player, "battles", {})
    return [str(battle_id) for battle_id in battles]


async def _run_attempt(config: BotConfig, remaining: int, progress: dict[str, Any]) -> int:
    player = RandomPlayer(server_configuration=config.server)
    try:
        await asyncio.wait_for(
            player.ladder(remaining),
            timeout=config.battle_timeout_seconds * max(remaining, 1),
        )
    finally:
        new_ids = [
            battle_id
            for battle_id in _battle_ids(player)
            if battle_id not in progress["completed_battle_ids"]
        ]
        progress["completed_battle_ids"].extend(new_ids)
        progress["completed_count"] = len(progress["completed_battle_ids"])
        _save_progress(config.data_dir / "progress.json", progress)
        await player.ps_client.stop_listening()
    return len(new_ids)


async def run_phase0(config: BotConfig) -> int:
    """Run until the configured number of distinct battle IDs is complete."""
    config.data_dir.mkdir(parents=True, exist_ok=True)
    initialize_database(config.data_dir / "battles.sqlite3")
    progress_path = config.data_dir / "progress.json"
    progress = _load_progress(progress_path)
    attempts = 0
    while progress["completed_count"] < config.battles:
        attempts += 1
        remaining = config.battles - progress["completed_count"]
        try:
            completed = await _run_attempt(config, remaining, progress)
            if completed == 0:
                raise RuntimeError("ladder attempt completed without a battle ID")
        except Exception:
            LOGGER.exception("Phase 0 attempt %s failed; reconnecting", attempts)
            if attempts >= config.retry_limit:
                raise
            await asyncio.sleep(config.backoff_seconds * attempts)
    return progress["completed_count"]


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    completed = asyncio.run(run_phase0(load_config()))
    LOGGER.info("Phase 0 complete: %s distinct battles", completed)


if __name__ == "__main__":
    main()
