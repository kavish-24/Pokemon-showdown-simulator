PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS raw_logs (
    battle_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    ts TEXT NOT NULL,
    side TEXT,
    raw_line TEXT NOT NULL,
    PRIMARY KEY (battle_id, seq)
);

CREATE TABLE IF NOT EXISTS structured_turns (
    battle_id TEXT NOT NULL,
    turn INTEGER NOT NULL,
    my_side TEXT NOT NULL,
    state_json TEXT NOT NULL,
    my_action TEXT,
    opp_action TEXT,
    outcome_json TEXT,
    PRIMARY KEY (battle_id, turn)
);

CREATE INDEX IF NOT EXISTS idx_raw_logs_battle_ts
    ON raw_logs (battle_id, ts);

CREATE INDEX IF NOT EXISTS idx_structured_turns_battle_turn
    ON structured_turns (battle_id, turn);

