# Copilot Instructions for Python Code

When generating or modifying Python code in this repository, follow these rules:

## 1. Use Python Type Hints

- Add type hints to all function and method parameters.
- Add return type annotations to all functions and methods.
- Prefer precise built-in and typing module types (for example, `list[str]`, `dict[str, int]`, `Iterable[Point]`).

## 2. Follow PEP 8 Naming Conventions

- Use `snake_case` for variables, functions, and methods.
- Use `PascalCase` for classes.
- Use `UPPER_CASE` for constants.
- Use descriptive names and avoid unclear abbreviations.

## 3. Always Include Docstrings

- Include a docstring for every function and method.
- Docstrings must include `Args` and `Returns` sections.
- Keep docstrings concise and focused on behavior, inputs, and outputs.

## 4. Treat This Project as a PyScript Browser Game

- Assume Python code runs in the browser through PyScript/Pyodide.
- Favor browser-safe patterns and avoid server-only assumptions.
- Keep Python and JavaScript responsibilities clear and minimal.

## 5. Use `js` Module Imports for DOM Interactions

- For DOM access and browser APIs, import from the `js` module (for example, `from js import document, window`).
- Do not replace `js` imports with non-browser abstractions for DOM operations.
- Keep DOM event binding and UI updates explicit and readable.

## 6. Encapsulate Game State in `SnakeCashRush`

- Keep mutable game state inside the `SnakeCashRush` class.
- Avoid introducing global mutable state for gameplay data.
- Prefer instance methods and instance fields for state transitions, rendering state, and input-driven updates.
- If helper functions are needed, keep them stateless and pass required values explicitly.

### Docstring Template

```python
def example(name: str) -> str:
    """Brief summary.

    Args:
        name: Description of the input.

    Returns:
        Description of the returned value.
    """
    return name
```
