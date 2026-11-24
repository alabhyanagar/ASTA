# CLAUDE.md — ASTA Development & Environment Guide

## Project Overview
ASTA (Autonomous Software Testing Platform) is a local-first software testing platform that inspects codebases, generates deterministic reviewable test plans, executes tests in isolated workers, and produces consolidated evidence-backed reports.

---

## Python Environment & Virtualenv

This project uses a dedicated Python 3.12 virtual environment located in `.venv/`.

### Activating the Environment
- **Windows PowerShell:**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows Command Prompt (cmd):**
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- **Linux / WSL / macOS:**
  ```bash
  source .venv/bin/activate
  ```

---

## Running Commands with Virtual Environment Python

Always invoke the virtualenv binary directly to ensure reproducible execution across tooling:

### 1. Running Tests
```powershell
# Run all tests using venv
.\.venv\Scripts\python.exe -m pytest

# Run with concise output
.\.venv\Scripts\python.exe -m pytest -q

# Run specific test file
.\.venv\Scripts\python.exe -m pytest tests/test_planner.py -v
```

### 2. Installing / Updating Dependencies
```powershell
# Using uv (fastest)
uv pip install -e .
uv pip install -r requirements.txt

# Or using venv directly
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Running ASTA CLI
```powershell
.\.venv\Scripts\python.exe -m asta.cli --help
```

---

## Development Guidelines
- **Deterministic Evaluator:** Never allow AI to determine pass/fail verdicts. Statuses must derive strictly from tool outputs and exit codes.
- **Strict Scope Boundaries:** No tests execute outside explicitly approved user scope.
- **Typing & Validation:** Use Pydantic v2 schemas and models. Avoid treating Pydantic models as dictionaries.
