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

## Playwright automation

The LLM API base URL defaults to
`https://6e12-35-247-101-12.ngrok-free.app` and can be overridden with
`LLM_API_BASE_URL`. Each request is independent and sends only a `question`
field. The model must return a JSON object using one of these actions:
`navigate`, `click`, `fill`, `type`, `wait`, `extract`, or `finish`.
Selectors and URLs are validated before use. Click, fill, and type actions
require an interactive confirmation in the terminal.
If the model returns ordinary text instead of an action object, the workflow
does not treat that text as success or execute it; it requests a strict action
JSON response again until the step limit is reached.

Run a task with an optional initial URL:

```powershell
.\venv\Scripts\python.exe .\main.py "Find the current page title" --url https://example.com
.\venv\Scripts\python.exe .\main.py "Search for Playwright documentation" --headed
```

Set `LLM_API_TIMEOUT_SECONDS`, `LLM_API_RETRIES`, and `AUTOMATION_MAX_STEPS`
to tune request and workflow limits. API errors, malformed responses, and
invalid model actions stop the workflow rather than being treated as success.
Known site selectors are loaded from [selectors.json](./selectors.json)
and included as selector hints in the model context. Override the file with
`AUTOMATION_SELECTORS_FILE` when needed.
The model is free to choose the next safe action based on the current page.
For example, it can wait for and click the `choose_username` selector before
filling the login fields when that button is present.
The page context also contains a fresh `interactive_elements` catalog with
numeric IDs and visible labels. Prefer actions such as
`{"action":"click_element","id":7}`; IDs are recollected after each step so
they do not become stale. Fuzzy matching is used only as a fallback for a
text query and requires a confidence score of at least 60. No MCP tool is
required; Playwright performs the live page lookup directly.

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

The model can request `fill_secret` using either configured variable name,
but secret values are injected locally and are never sent to the LLM API or
included in page-context logs. Login clicks and credential entry require
terminal confirmation.

## Later phases

- TODO(phase-1): Add baseline agents and Wilson confidence intervals.
- TODO(phase-2): Persist every raw protocol line and derive structured turns.
- TODO(phase-3): Implement belief-state priors and damage/speed calculations.
- TODO(phase-4): Add legal-action search with Tera opportunity cost.
- TODO(phase-5): Train the evaluator and opponent model.
- TODO(phase-6): Add the optional Ollama advisor.
- TODO(phase-7): Add throttled ladder operation and production recovery.
