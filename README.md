# Jev Ticketing System Demo

A command-line support-ticket system that uses **Jev**, TypeSafe AI's "System One"
decision model, to automatically triage incoming tickets.

## How it works

```
New ticket ──► Jev (one parallel call, 4 typed questions) ──► Router (plain Python) ──► Queue
                 • category  (Choice)                           • picks team queue
                 • priority  (Score, 0–3)                       • sets SLA hours
                 • escalate? (Noul = yes/no probability)        • flags escalations
                 • refund?   (Noul)                             • low confidence → Manual Review
```

Jev decides **what** a ticket is; `app/router.py` decides **what to do** about it.

## Project layout

```
jev-ticketing-demo/
├── main.py                 # CLI menu (entry point)
├── app/
│   ├── models.py           # Ticket + TriageResult dataclasses
│   ├── jev_triage.py       # Jev questions, real client, offline mock
│   ├── router.py           # Routing / SLA / escalation rules
│   ├── store.py            # JSON-file storage (data/tickets.json)
│   └── service.py          # Glues everything together
├── data/sample_tickets.json
├── tests/test_router.py
└── .vscode/                # Run config + pytest setup
```

## Setup in VS Code

1. **Open the folder:** File → Open Folder → `jev-ticketing-demo`.
2. **Install the Python extension** if VS Code prompts you.
3. **Create a virtual environment** in the VS Code terminal (Terminal → New Terminal):

   Windows:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   macOS / Linux:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Then press `Ctrl+Shift+P` → **Python: Select Interpreter** → pick `.venv`.
   (Python 3.10+ required.)

4. **(Optional) Add your Jev API key:** copy `.env.example` to `.env` and paste your key.
   Without a key the app runs in **offline mock mode** with keyword rules, so the demo
   always works.

5. **Run it:** press `F5` (uses `.vscode/launch.json`, which loads `.env`) or
   `python main.py` in the terminal. Choose option **5** to load sample tickets,
   then **2** to see the routed list.

6. **Run tests:** `pytest`, or use the Testing (beaker) panel in VS Code.

## Getting Jev access

Keys come from the TypeSafe console (https://console.typesafe.ai/keys). Access was in
early access/waitlist as of late September 2026, so check typesafe.ai for the current
status. Jev is also offered through Vercel AI Gateway, Cloudflare Workers AI, and OpenRouter.

## Ideas to extend it

- Add a `sentiment` Score question and show angry customers first
- Swap the CLI for a Flask or FastAPI web UI
- Use `AsyncTypeSafeClient` to triage hundreds of tickets in parallel
- Store tickets in SQLite instead of JSON
