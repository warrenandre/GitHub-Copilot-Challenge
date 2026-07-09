# Copilot Instructions

When generating or modifying Python code in this repository, follow these rules:

1. Use Python type hints for function signatures, return values, variables where helpful, and class attributes where appropriate.
2. Follow PEP 8 naming conventions:
   - `snake_case` for variables, functions, and methods
   - `CapWords` (PascalCase) for classes
   - `UPPER_CASE` for constants
3. Always include docstrings for modules, classes, and functions.
4. Function and method docstrings must include these sections:
   - Args
   - Returns
5. Treat this project as a PyScript browser game.
6. For DOM interactions in Python, use imports from the `js` module (for example, `from js import document`).
7. Encapsulate all game state in the `SnakeCashRush` class. Avoid global mutable state for gameplay data.

Use clear, concise docstrings that accurately describe behavior, inputs, and outputs.