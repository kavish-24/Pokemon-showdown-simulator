import json
import logging
import re
from ast import literal_eval

from pydantic import ValidationError

from src.agent.models import Action

LOGGER = logging.getLogger(__name__)


def parse_action(answer: str, fallback_secret: str | None = None) -> Action:
    LOGGER.debug(
        "Parsing LLM action response: length=%d preview=%r",
        len(answer),
        answer[:500],
    )
    decoder = json.JSONDecoder()
    for index, character in enumerate(answer):
        if character == "{":
            try:
                payload, _ = decoder.raw_decode(answer[index:])
                return Action.model_validate(payload)
            except json.JSONDecodeError:
                continue
            except ValidationError:
                raise
    for match in re.finditer(r"\{[^{}]+\}", answer, re.DOTALL):
        try:
            payload = literal_eval(match.group(0))
        except (SyntaxError, ValueError):
            continue
        if isinstance(payload, dict):
            return Action.model_validate(payload)
    command = answer.strip().strip("`").strip()
    click_match = re.fullmatch(r"(?:click|click_element)\s*\(\s*(\d+)\s*\)", command, re.IGNORECASE)
    if click_match:
        return Action(action="click_element", id=int(click_match.group(1)))
    secret_match = re.fullmatch(
        r"fill_secret\s*\(\s*['\"]?(POKEMON_SHOWDOWN_USERNAME|POKEMON_SHOWDOWN_PASSWORD)['\"]?\s*\)",
        command,
        re.IGNORECASE,
    )
    if secret_match:
        return Action(action="fill_secret", secret=secret_match.group(1).upper())
    if fallback_secret and re.search(r"\b(fill|enter|type|input)\b", answer, re.IGNORECASE):
        return Action(action="fill_secret", secret=fallback_secret)
    LOGGER.warning(
        "LLM action parsing failed: length=%d starts_with=%r has_json_marker=%s",
        len(answer),
        answer[:80],
        "{" in answer or "```" in answer,
    )
    raise ValueError(
        f"LLM response did not contain a valid action JSON object "
        f"(length={len(answer)}, preview={answer[:160]!r})."
    )
