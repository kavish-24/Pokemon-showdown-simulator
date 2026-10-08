"""Initialize the Phase 0 SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import load_config


def initialize_database(path: Path) -> None:
    """Create the schema and enable WAL mode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(path) as connection:
        connection.executescript(schema)
        connection.commit()


def main() -> None:
    config = load_config()
    initialize_database(config.data_dir / "battles.sqlite3")


if __name__ == "__main__":
    main()

