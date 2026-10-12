import pytest
from pydantic import ValidationError

from src.agent.llm.parsing import parse_action


def test_parse_action_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        parse_action('{"action":"click_element","id":1,"code":"eval()"}')


def test_parse_action_accepts_legacy_secret_command():
    action = parse_action("fill_secret('POKEMON_SHOWDOWN_USERNAME')")
    assert action.action == "fill_secret"
    assert action.secret == "POKEMON_SHOWDOWN_USERNAME"


def test_parse_action_extracts_json():
    action = parse_action('Here: {"action":"click_element","id":2}')
    assert action.action == "click_element"
    assert action.id == 2


def test_parse_action_accepts_single_quoted_json():
    action = parse_action("```{'action': 'fill_secret', 'secret': 'POKEMON_SHOWDOWN_USERNAME'}```")
    assert action.action == "fill_secret"
    assert action.secret == "POKEMON_SHOWDOWN_USERNAME"


def test_parse_action_uses_safe_secret_fallback_for_prose():
    action = parse_action("Fill the username input now.", "POKEMON_SHOWDOWN_USERNAME")
    assert action.action == "fill_secret"
    assert action.secret == "POKEMON_SHOWDOWN_USERNAME"


def test_parse_action_does_not_infer_from_instruction_only_response():
    with pytest.raises(ValueError):
        parse_action("Do not add extra text. Just return the JSON object.")
