# Gen 9 Random Battle bot

This project is being built phase by phase. The current implementation is Phase 0
only: an env-driven `poke-env` random player, a minimal SQLite schema, and a
placeholder belief-state API. It does not use Playwright or Chrome.

## Setup

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `SHOWDOWN_WS_URL` and `SHOWDOWN_AUTH_URL` for the Kaggle/ngrok server or a
local Showdown server. The code defaults to localhost only when those variables
are unset. Set `DATA_DIR` to `/kaggle/working/data` on Kaggle.

## Phase 0

Initialize the database:

```powershell
.\venv\Scripts\python.exe -m src.db.init_db
```

Run 100 unattended Gen 9 Random Battles:

```powershell
.\venv\Scripts\python.exe -m src.phase0_bot
```

The runner stores progress in `DATA_DIR/progress.json`, skips completed battle
IDs on restart, and writes the SQLite database with WAL mode enabled. A retry
creates a fresh `RandomPlayer` after a connection or ladder failure.

The Phase 0 exit test is a 100-battle unattended run against the configured
server. The bot chooses random legal actions supplied by `poke-env`; it does not
infer hidden moves, items, abilities, HP, or outcomes.

## Later phases

- TODO(phase-1): Add baseline agents and Wilson confidence intervals.
- TODO(phase-2): Persist every raw protocol line and derive structured turns.
- TODO(phase-3): Implement belief-state priors and damage/speed calculations.
- TODO(phase-4): Add legal-action search with Tera opportunity cost.
- TODO(phase-5): Train the evaluator and opponent model.
- TODO(phase-6): Add the optional Ollama advisor.
- TODO(phase-7): Add throttled ladder operation and production recovery.

