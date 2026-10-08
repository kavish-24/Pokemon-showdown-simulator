import sqlite3

from src.db.init_db import initialize_database


def test_schema_creates_tables_and_wal(tmp_path):
    database = tmp_path / "battles.sqlite3"
    initialize_database(database)
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    assert {"raw_logs", "structured_turns"} <= tables
    assert journal_mode.lower() == "wal"

