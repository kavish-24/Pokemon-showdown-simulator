"""Command-line entry point for the Playwright automation workflow."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from dotenv import load_dotenv

from src.automation import AutomationConfig, AutomationWorkflow
from src.llm_client import LlmClient


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an LLM-guided browser automation task.")
    parser.add_argument("task", help="The automation task to perform.")
    parser.add_argument(
        "--url",
        help="Optional initial HTTP(S) URL. The model may request navigation to another validated URL.",
    )
    parser.add_argument("--headed", action="store_true", help="Show the browser window.")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=int(os.getenv("AUTOMATION_MAX_STEPS", "8")),
        help="Maximum observe/request/action iterations.",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    config = AutomationConfig.from_environment(headless=not args.headed, max_steps=args.max_steps)

    async def confirm(prompt: str) -> bool:
        answer = await asyncio.to_thread(input, f"{prompt} [y/N] ")
        return answer.strip().lower() in {"y", "yes"}

    async with LlmClient(config.llm_base_url, timeout_seconds=config.llm_timeout_seconds) as llm:
        workflow = AutomationWorkflow(llm, config, confirm_action=confirm)
        result = await workflow.run(args.task, args.url)
    logging.getLogger(__name__).info("Automation finished: %s", result.status)
    if result.message:
        print(result.message)
    return 0 if result.success else 1


def main() -> None:
    args = _parser().parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
