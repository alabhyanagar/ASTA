# ASTA Project Rules

## Architecture & Scope
- `asta/`: Core engine (`audit.py`, `capability.py`, `cli.py`, `credentials.py`, `inspection.py`, `language_boundary.py`, `models.py`, `persistence.py`, `planner.py`, `recommendation.py`, `schema.py`, `scope.py`, `state_machine.py`, `taxonomy.py`, `toml_validator.py`) and CLI subcommands (`asta/commands/`).
- `tests/`: Pytest suite (`test_capability.py`, `test_inspection.py`, `test_language_boundary.py`, `test_models.py`, `test_planner.py`, `test_recommendation.py`, `test_taxonomy.py`).
- Never scan or search `Other-Older-demo-ref-docs/`, `work/`, `final-docs/`, `.venv/`, or `uv.lock` unless explicitly asked. Always scope `Grep` and `Glob` to `asta/` and `tests/`.

## Running Tests & CLI
- Always run Python commands via `uv run` to use `.venv` (never invoke global `python` or bare `pytest`):
  - Single test file: `uv run pytest tests/test_capability.py -q`
  - Single test case: `uv run pytest tests/test_capability.py -k "test_name" -q`
  - CLI check: `uv run asta --help`

## Strict File Editing Rules (Fixes Update Mismatches)
1. ALWAYS call `Read` with explicit `offset` and `limit` on the exact target lines immediately before calling `Edit` (`Update`).
2. Keep `old_string` minimal (3–5 unique lines). Never pass large multi-function blocks to `Edit`.
3. If `Edit` fails with `String to replace not found in file`, do NOT retry the same `Edit` call. Immediately `Read` the exact line range to check indentation/comments and retry once.

## Tool & MCP Routing
- Use `context7` (`resolve-library-id` -> `query-docs`) ONLY when verifying unfamiliar third-party Python APIs (e.g., `schemathesis`, `pytest`, `pydantic`). Do not call it for internal `asta` modules.
- Keep responses and code diffs concise. Do not rewrite untouched functions.

## File Editing Rules
- ALWAYS run `Read` on the target file section immediately before calling `Edit` (`Update`) to verify exact indentation, comments, and whitespace.
- Keep `old_string` minimal (3–5 unique lines) rather than large multi-line blocks.
- If `Edit` fails with "String to replace not found in file", do NOT retry the same `Edit` call. Immediately `Read` the exact line range and retry once, or rewrite the file using `Write`.