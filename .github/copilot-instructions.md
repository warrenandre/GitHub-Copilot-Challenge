# Project Guidelines

## Code Style

- Use Python type hints for function parameters, return values, and important variables when it improves clarity.
- Follow PEP 8 naming conventions:
  - `snake_case` for functions, variables, and module-level names.
  - `PascalCase` for class names.
  - `UPPER_SNAKE_CASE` for constants.
- Write docstrings for all public functions, methods, and classes.
- Function and method docstrings must include:
  - `Args`: each parameter with a short description.
  - `Returns`: the return type/shape and meaning.

## Conventions

- Prefer clear, descriptive names over abbreviations.
- Keep functions focused and small when practical.
- Keep docstrings concise, accurate, and synchronized with the implementation.

## Project-Specific Rules

- This project is a PyScript browser game.
- For browser DOM interactions in Python, use imports from the `js` module (for example, `from js import document`) instead of non-PyScript patterns.
- Encapsulate all game state in the `SnakeCashRush` class. Avoid introducing global mutable game state outside this class.
