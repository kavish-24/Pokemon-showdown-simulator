import argparse
import asyncio
import logging
import os
from pathlib import Path

from src.agent.config import Settings
from src.agent.llm.http_client import HttpLlmClient
from src.agent.orchestrator import Orchestrator


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("--url", default="https://play.pokemonshowdown.com/")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    settings = Settings.from_env(root)
    settings.browser_headless = not args.headed

    async def confirm(prompt: str) -> bool:
        return (await asyncio.to_thread(input, f"{prompt} [y/N] ")).strip().lower() in {"y", "yes"}

    async def run() -> None:
        async with HttpLlmClient(
            settings.api_base_url,
            timeout_seconds=settings.api_timeout_seconds,
            retries=settings.api_retries,
        ) as llm:
            result = await Orchestrator(settings, llm, confirm).run(args.task, args.url)
        print(result.message)
        if not result.success:
            raise SystemExit(1)

    asyncio.run(run())
