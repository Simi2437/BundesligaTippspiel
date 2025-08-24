# AGENTS.md

## Build, Lint, and Test Commands

- **Build/Run (Docker):**
  - `docker-compose build`
  - `docker-compose up -d`
- **Run Main App (local):**
  - `python app/main.py`
- **Run with Dockerfile:**  
  - Builds Python 3.11-slim, installs requirements, exposes port 8080 for NiceGUI.
- **Testing:**
  - Use `pytest` for tests (installed in `.venv`).
  - Run all tests: `.venv/bin/pytest`
  - Run a single test: `.venv/bin/pytest path/to/test_file.py::test_function`
- **Linting:**
  - No linter config found; recommend using `flake8` or `black` for style.

## Code Style Guidelines

- **Imports:**  
  - Use absolute imports (e.g., `from app.backend.models.user import ...`).
  - Standard library imports first, then third-party, then local.
- **Formatting:**  
  - 4 spaces per indentation.
  - Max line length: 120 (recommended).
- **Types:**  
  - Use type hints for function arguments and return values where possible.
  - Prefer explicit types for public APIs.
- **Naming Conventions:**  
  - Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
  - Variables: `snake_case`
- **Error Handling:**  
  - Use try/except for database and external service calls.
  - Log errors with `print()` or `traceback.print_exc()`.
  - Return `None` or `False` for failed operations.
- **Other:**  
  - Use docstrings for public functions.
  - Avoid global state except for database connections.
  - Prefer explicit over implicit behavior.
