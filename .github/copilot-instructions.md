# GitHub Copilot Instructions

These instructions define the coding standards, naming conventions, and architectural patterns for this project. All Copilot suggestions must conform to these rules.

---

## Project Context

This is a **PyScript browser game** called **Snake Cash Rush**. The game logic is written entirely in Python and runs client-side in the browser via [PyScript](https://pyscript.net). There is no backend server.

**Tech stack:**
- **Python** (game logic) via PyScript 2025.3.1
- **HTML/CSS/JavaScript** (UI shell and DOM bootstrap)
- **PyScript `js` module** for all DOM and browser API interactions
- **`pyodide.ffi.create_proxy`** for wrapping Python callables passed to JavaScript event listeners

---

## Python Code Style

### Type Hints
- Always use Python type hints on all function signatures (parameters and return types).
- Use `from __future__ import annotations` at the top of every Python file to enable postponed evaluation.
- Use built-in generic types (`list[int]`, `dict[str, int]`) instead of `typing.List`, `typing.Dict`.
- Use `|` union syntax (e.g., `int | None`) instead of `Optional[int]`.

```python
# Correct
def move(self, direction: Point) -> None: ...
def spawn_cash(self, occupied: list[Point]) -> Point: ...

# Incorrect
def move(self, direction) -> None: ...
from typing import Optional
def get_score(self) -> Optional[int]: ...
```

### Docstrings
- Every public method and function must have a docstring.
- Use the following format with **Args** and **Returns** sections:

```python
def spawn_cash(self, occupied: list[Point]) -> Point:
    """Spawn a cash pickup in a random unoccupied board cell.

    Args:
        occupied: A list of Points currently occupied by the snake.

    Returns:
        A Point representing the new cash pickup position.
    """
```

- Single-line docstrings are acceptable only for trivially obvious properties or `__repr__`.
- Docstrings go immediately after the `def` line, before any code.

### Naming Conventions (PEP 8)
| Construct | Convention | Example |
|---|---|---|
| Module | `snake_case` | `main.py` |
| Class | `PascalCase` | `SnakeCashRush`, `Point` |
| Method / Function | `snake_case` | `reset_state`, `handle_keydown` |
| Variable | `snake_case` | `tick_ms`, `best_score` |
| Constant (module-level) | `UPPER_SNAKE_CASE` | `GRID_SIZE`, `BASE_TICK_MS` |
| Private attribute | `_snake_case` (single leading underscore) | `_key_proxy`, `_frame_proxy` |

- Do **not** use camelCase for Python identifiers.
- Do **not** abbreviate names unless the abbreviation is universally understood (`ctx`, `ms`, `id`).

### General Style
- Follow [PEP 8](https://peps.python.org/pep-0008/) for all formatting: 4-space indentation, max 99 chars per line, two blank lines between top-level definitions.
- Prefer `dataclasses.dataclass` for plain data containers.
- Use `frozen=True` on dataclasses that represent immutable value objects (e.g., `Point`).
- Avoid mutable default arguments.

---

## Architecture: SnakeCashRush Class

### Encapsulation Rule
**All game state must be encapsulated inside the `SnakeCashRush` class.** Do not use module-level mutable variables to hold game state.

This includes:
- Snake body segments (`self.snake`)
- Current direction and pending direction (`self.direction`, `self.pending_direction`)
- Score and best score (`self.score`, `self.best_score`)
- Cash pickup position (`self.cash`)
- Timing state (`self.tick_ms`, `self.accumulator`, `self.last_frame_time`)
- Game lifecycle flags (`self.running`, `self.game_over`)

### DOM Interactions
- **Always use the `js` module** for DOM interactions. Never use `document` or `window` from any other source.
- Import pattern:

```python
from js import document, window  # type: ignore[import-not-found]
```

- Wrap any Python callable passed to a JavaScript API (event listeners, `requestAnimationFrame`, window-exposed functions) with `create_proxy`:

```python
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]

self._key_proxy = create_proxy(self.handle_keydown)
document.addEventListener("keydown", self._key_proxy)
```

- **Never pass a raw Python function** directly to a JavaScript API without `create_proxy`.
- Store all proxies as instance attributes (e.g., `self._key_proxy`) so they are not garbage-collected.

### Initialisation Pattern
- `__init__` is responsible for: acquiring DOM element references, reading persisted state, wiring event listeners, and calling `reset_state()` followed by `draw()`.
- `reset_state()` must restore all transient game state to its initial values without re-querying the DOM.

---

## JavaScript / App Bootstrap (app.js)

- `app.js` is a **vanilla JS bootstrap file** only. It must not contain game logic.
- It provides the `snakeCashRushBridge` object on `window` for localStorage access.
- Keep it minimal: localStorage read/write helpers and any pre-PyScript DOM prep only.

---

## HTML / CSS

- HTML element IDs use `camelCase` (e.g., `gameCanvas`, `scoreValue`, `overlayKicker`).
- CSS classes use `kebab-case` (e.g., `game-card`, `score-tile`, `cash-burst`).
- Do not use inline styles; all styling goes in `styles.css`.

---

## File Structure

```
games/snake/src/
  main.py       # Python game logic — SnakeCashRush class and entry point
  index.html    # HTML shell — loads PyScript, app.js, styles.css
  app.js        # JS bootstrap — bridge object and localStorage helpers
  styles.css    # All styles
```

New game features belong in `main.py`. New UI elements belong in `index.html` + `styles.css`. Do not create additional source files unless adding a genuinely separate Python module.

---

## Testing & Correctness Priorities

When generating new game logic, ensure:
1. Direction changes prevent illegal instant 180° reversal.
2. Wall and self-collision detection uses the full board boundary.
3. Cash spawning only targets cells not occupied by any snake segment.
4. Restart logic fully resets all transient state via `reset_state()`.
5. Best score is only updated when the current score strictly exceeds it.
