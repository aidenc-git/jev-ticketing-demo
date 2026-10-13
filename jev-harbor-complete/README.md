# JEV Ticketing — integration tests

This package includes the six uploaded application source files plus tests. It does **not** run the Harbor framework; it provides verified local integration tests as a prerequisite for a Harbor task. No Docker or API key is needed for these offline tests.

## Windows / VS Code

Extract the ZIP, open `jev-harbor-complete` in VS Code, and run:

```powershell
python -m pip install pytest
$env:JEV_MOCK='1'
python -m pytest tests -v
python main.py
```

The tests use temporary storage and mocked API failures, so they do not change your actual `data/tickets.json`. `main.py` runs the demo; to load sample tickets, the original `data/sample_tickets.json` must be present (it was not among the uploaded files).

## Add tests to your existing project

Copy only `tests/test_integration.py` into the existing `jev-ticketing-demo/tests` directory and run `python -m pytest tests/test_integration.py -v` from the project root. Your original application source files can remain unchanged.

## Live JEV / Harbor

Live JEV tests require valid `TYPESAFE_API_KEY` and the `typesafe-sdk` dependency. Do not commit your key. The `get_triager()` function switches to offline mock when the key is absent or `JEV_MOCK=1`.

A genuine Harbor run requires configuring an actual Harbor task, verifier, agent and supported execution environment. These local tests alone do not constitute a Harbor evaluation.
