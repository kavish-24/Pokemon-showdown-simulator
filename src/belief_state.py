"""Belief-state API skeleton for later phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class BeliefState:
    """Known facts and possible opponent sets.

    Phase 0 deliberately stores no inferred facts. Later phases must keep
    unknown values unknown and source priors from Random Battle set data.
    """

    known: dict[str, Any] = field(default_factory=dict)
    possible_sets: dict[str, dict[str, float]] = field(default_factory=dict)

    def update_from_move(self, pokemon: str, move: str) -> None:
        """Update a revealed move. Implemented in Phase 3."""
        raise NotImplementedError

    def update_from_item(self, pokemon: str, item: str) -> None:
        """Update a revealed or consumed item. Implemented in Phase 3."""
        raise NotImplementedError

    def update_from_ability(self, pokemon: str, ability: str) -> None:
        """Update a revealed ability. Implemented in Phase 3."""
        raise NotImplementedError

    def update_from_tera(self, pokemon: str, tera_type: str) -> None:
        """Update a revealed Tera type. Implemented in Phase 3."""
        raise NotImplementedError

    def update_from_damage(
        self,
        attacker: str,
        defender: str,
        damage: int | float,
        defender_hp: int | float,
    ) -> None:
        """Update damage evidence without inventing hidden state."""
        raise NotImplementedError

    def legal_possible_sets(self, pokemon: str) -> Mapping[str, float]:
        """Return legal possible sets and probabilities in a later phase."""
        raise NotImplementedError

    def sample_set(self, pokemon: str, seed: int | None = None) -> str:
        """Sample one possible set using later-phase priors."""
        raise NotImplementedError

