# Copilot Instructions

- Use Python type hints for all function parameters and return values.
- Follow PEP 8 naming conventions (snake_case for functions/variables, PascalCase for classes).
- Always include docstrings on classes and functions with `Args:` and `Returns:` sections.
- This is a PyScript browser game; Python code runs in the browser via Pyodide.
- Use `from js import document, window` for all DOM interactions (never raw JavaScript).
- All game state must be encapsulated in the `SnakeCashRush` class; avoid module-level mutable state.
