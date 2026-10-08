import pytest

from src.belief_state import BeliefState


def test_belief_state_does_not_invent_facts():
    state = BeliefState()
    assert state.known == {}
    with pytest.raises(NotImplementedError):
        state.update_from_move("opponent", "unknown")

