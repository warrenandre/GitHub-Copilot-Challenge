# Copilot Instructions

When generating or modifying Python code in this repository, follow these rules:

1. Use Python type hints for all function and method parameters and return values.
2. Follow PEP 8 naming conventions:
   - `snake_case` for variables, functions, and module names
   - `PascalCase` for class names
   - `UPPER_SNAKE_CASE` for constants
3. Always include docstrings for functions and methods with the following sections:
   - `Args:`
   - `Returns:`
4. This project is a PyScript browser game; prioritize patterns and APIs appropriate for browser-executed Python.
5. For DOM interactions in Python, use `js` module imports (for example `from js import document`) rather than non-browser abstractions.
6. Encapsulate all game state inside the `SnakeCashRush` class; avoid module-level mutable game state.
