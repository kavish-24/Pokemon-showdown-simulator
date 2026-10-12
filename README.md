# Gen 9 Random Battle bot

This project contains the Phase 0 `poke-env` random player and an independent
LLM-guided browser automation entry point using Playwright. The automation
workflow observes the current page, sends a task plus bounded page context to
the stateless `/predict` API, validates the returned JSON action, and executes
only supported Playwright operations.

## Setup

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m playwright install chromium
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

## Playwright SOP automation

The modular agent in [src/agent/](./src/agent/) runs the data-driven SOP in
[config/sops/login.yaml](./config/sops/login.yaml). Code checks the DOM to
verify each step; the LLM only selects one allowed action for the current
step. Page text is treated as untrusted data, credentials are referenced by
allowlisted environment-variable names, and state is saved after every
action to `.agent/run-state.json`.

The LLM API base URL defaults to
`https://2f61-146-148-48-224.ngrok-free.app` and can be overridden with
`LLM_API_BASE_URL`. Each stateless request sends exactly a JSON object with a
`question` field. Timeout, retry, invalid JSON, HTTP errors, and missing
`answer` fields are reported as failures.

Configure credentials in `.env`:

For Pokémon Showdown login automation, set these values in `.env`:

```env
POKEMON_SHOWDOWN_USERNAME=your_username
POKEMON_SHOWDOWN_PASSWORD=your_password
```

Then run a task such as:

```powershell
.\venv\Scripts\python.exe .\main.py `
  "Open Pokémon Showdown, choose a username, enter the configured username and password, and log in" `
  --url https://play.pokemonshowdown.com/ `
  --headed
```

The model can request `fill_secret` using either configured variable name, but
secret values are injected locally and never sent to the LLM API or logs.
Credential entry does not ask for confirmation. Clicks still require
confirmation. Each invocation starts the Login SOP from the beginning, even
when a previous run state exists. Once the visible login control is gone, the
login SOP is marked successful, the Playwright browser closes, and the process
exits. The saved state retains the run history for inspection.

The planned task states are `Login`, `start a match`, `play the match`, and
`exit from the browser`; only `Login` is implemented currently. Add another
SOP under `config/sops/` to support a future workflow without changing the
core orchestrator.

## Later phases

- TODO(phase-1): Add baseline agents and Wilson confidence intervals.
- TODO(phase-2): Persist every raw protocol line and derive structured turns.
- TODO(phase-3): Implement belief-state priors and damage/speed calculations.
- TODO(phase-4): Add legal-action search with Tera opportunity cost.
- TODO(phase-5): Train the evaluator and opponent model.
- TODO(phase-6): Add the optional Ollama advisor.
- TODO(phase-7): Add throttled ladder operation and production recovery.
