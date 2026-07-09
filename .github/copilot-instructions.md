# GitHub Copilot Instructions

These instructions apply to every file in this repository.
Follow them precisely when generating or modifying any code.

---

## Project Overview

**Snake Cash Rush** is a browser-based Snake game where all game logic is written in
**Python** and executed client-side via **PyScript** (WebAssembly/Pyodide).
A thin JavaScript bridge (`app.js`) handles browser-specific APIs that PyScript cannot
call directly.  There is no build step, no bundler, and no server-side code.

### Tech Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| Game logic | Python | 3.10+; run in-browser by PyScript |
| Browser runtime | PyScript | 2025.3.1 via CDN (`pyscript.net`) |
| JS↔Python bridge | Pyodide FFI | `from pyodide.ffi import create_proxy` |
| DOM access | Pyodide JS bindings | `from js import document, window` |
| Rendering | HTML5 Canvas 2D | Drawn from Python via `js.document` |
| Persistence | Web Storage | `window.localStorage` via JS bridge |
| Styling | Vanilla CSS | CSS custom properties, no framework |
| JS helpers | Vanilla JS | `app.js` only; no libraries or bundler |

---

## Python — Naming Conventions

Follow **PEP 8** strictly.

- **Classes**: `PascalCase` — e.g. `SnakeCashRush`, `Point`
- **Methods and functions**: `snake_case` — e.g. `reset_state`, `spawn_cash`
- **Variables and parameters**: `snake_case` — e.g. `next_head`, `tick_ms`
- **Constants** (module-level, immutable): `SCREAMING_SNAKE_CASE` — e.g. `BOARD_CELLS`, `BASE_TICK_MS`
- **Private / internal attributes**: prefix with a single underscore — e.g. `self._key_proxy`
- **Type aliases**: `PascalCase` when defined at module level

Never use single-letter variable names outside of very short loop counters (`i`, `x`, `y`).
Prefer descriptive names even when they are longer.

---

## Python — Type Hints

- **Always** annotate function/method parameters and return types.
- Use `from __future__ import annotations` at the top of every Python file so
  forward references resolve lazily and `X | Y` union syntax works on Python 3.10.
- Use the built-in generic forms (`list[int]`, `dict[str, int]`) not `List`, `Dict` from `typing`.
- Use `X | None` instead of `Optional[X]`.
- Use `typing.Iterable` / `typing.Sequence` for read-only collection parameters.

```python
# Correct
from __future__ import annotations
from typing import Iterable

def spawn_cash(self, snake: Iterable[Point]) -> Point: ...

# Incorrect — do not do this
from typing import Optional, List
def spawn_cash(self, snake: List) -> Optional[Point]: ...
```

---

## Python — Docstrings

Every `class`, `def`, and module must have a docstring.

**Format**: Google style with explicit `Args:` and `Returns:` sections.

```python
def hit_wall(self, point: Point) -> bool:
    """Return True if the given grid point lies outside the playable area.

    The board spans columns 0..BOARD_CELLS-1 and rows 0..BOARD_CELLS-1.

    Args:
        point: The grid coordinate to test (typically the next head position).

    Returns:
        True if the point is out-of-bounds, False if it is inside the board.
    """
```

Rules:
- The first line is a single-sentence summary ending with a period.
- Leave one blank line between the summary and the body / Args section.
- Document every parameter and the return value, even obvious ones.
- If a method has no parameters beyond `self` and returns `None`, write a
  summary sentence and omit the `Args:` / `Returns:` sections.
- Nested helper functions (closures) must have at minimum a one-line docstring.

---

## Python — Inline Comments

Add inline or block comments whenever the *why* is not obvious from the code alone.
Required for:

- **PyScript / Pyodide patterns** — explain `create_proxy()`, JS bridge calls, and
  any workaround for browser sandbox limitations.
- **Game-loop math** — explain the fixed-timestep accumulator, speed formulas, and
  grid-to-pixel coordinate conversions.
- **Non-obvious collision logic** — e.g. tail-inclusion trick when the snake is about
  to collect a cash bill.
- **CSS animation retrigger patterns** — any sequence of class add/remove with
  `setTimeout` must explain the repaint-cycle requirement.
- **Magic numbers** — replace bare literals with named constants or explain them inline
  (e.g. `6.283  # 2π — full circle arc`).

---

## Python — Code Style

- Maximum line length: **100 characters**.
- Use **4-space indentation** (never tabs).
- Prefer `dataclass(frozen=True)` for simple value objects (e.g. `Point`).
- Prefer a single `dict` literal lookup over a chain of `if/elif` for key-to-value mappings.
- Do not use bare `except:` — always specify the exception type.
- Avoid mutable default arguments.
- Use f-strings for string interpolation; do not use `%` formatting or `.format()`.

---

## Architecture — Game State

**All mutable game state lives inside the `SnakeCashRush` class.**

- Do not use module-level variables for state that changes during gameplay
  (score, snake position, direction, tick speed, etc.).
- Module-level `SCREAMING_SNAKE_CASE` constants are the only exception.
- The single `game = SnakeCashRush()` line at the bottom of `main.py` is the only
  instantiation point.

---

## Architecture — PyScript / DOM Interaction

### Importing browser APIs

Always import DOM and window APIs from the `js` module:

```python
from js import document, window  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]
```

The `# type: ignore` comments suppress spurious type-checker warnings because these
modules only exist at runtime inside the PyScript/Pyodide environment.

### Wrapping Python callables for JS

**Every** Python callable passed to a JS API (event listeners, `setTimeout`,
`requestAnimationFrame`) **must** be wrapped with `create_proxy()`:

```python
# Correct — JS holds a strong Proxy reference; Python object stays alive
self._key_proxy = create_proxy(self.handle_keydown)
document.addEventListener("keydown", self._key_proxy)

# Incorrect — JS garbage-collector may collect the Python function
document.addEventListener("keydown", self.handle_keydown)
```

Store each proxy as an instance attribute (e.g. `self._key_proxy`) so it can be
released via `proxy.destroy()` if the game instance is torn down.

### JS Bridge pattern

Browser APIs that cannot be called directly from Python are exposed through the
`window.snakeCashRushBridge` object defined in `app.js`.
Python code must call these via `window.snakeCashRushBridge.<method>()`.

Current bridge methods:

| Method | Purpose |
|---|---|
| `raf(callback)` | `requestAnimationFrame` |
| `cancelRaf(handle)` | `cancelAnimationFrame` |
| `readBestScore()` | Read integer best score from `localStorage` |
| `writeBestScore(n)` | Persist best score to `localStorage` |

When adding new browser API calls, **extend the bridge in `app.js`** rather than
calling `window.*` directly from Python.

---

## Architecture — Game Loop

The game uses a **fixed-timestep accumulator** pattern:

1. `requestAnimationFrame` fires `game_frame(timestamp)` once per display refresh.
2. The elapsed milliseconds are added to `self.accumulator`.
3. The accumulator is drained in `self.tick_ms`-sized chunks by calling `advance()`.
4. This decouples game speed from display refresh rate (works correctly at 30, 60, or 144 Hz).

Do not replace this pattern with a simple `setInterval` approach.

---

## Architecture — Coordinate System

- Grid coordinates use a `Point(x, y)` frozen dataclass.
- `x` = column (0 = left, `BOARD_CELLS - 1` = right).
- `y` = row (0 = top, `BOARD_CELLS - 1` = bottom — y increases downward).
- Pixel coordinates are derived as `cell = BOARD_PIXELS / BOARD_CELLS; px = point.x * cell`.
- Direction vectors follow the same sign convention: up = `Point(0, -1)`, down = `Point(0, 1)`.

---

## JavaScript — Naming and Style

- Use **camelCase** for all JS variable names, function names, and object keys.
- Keep `app.js` minimal — only browser-API wrapper functions that Python cannot call directly.
- Do not import external JS libraries.
- Use `const` for values that do not change; `let` for values that do.
- Do not use `var`.

---

## CSS — Naming and Style

- Use **kebab-case** for all class names and custom property names.
- Define all colours and spacing tokens as CSS custom properties on `:root`.
- Do not use inline styles in HTML — all styling belongs in `styles.css`.
- Support dark mode by default (`color-scheme: dark` is already set on `:root`).

---

## File Structure Conventions

```
games/snake/
├── README.md           ← setup, gameplay guide, project structure
└── src/
    ├── index.html      ← page shell; no inline JS logic beyond PyScript bootstrap
    ├── styles.css      ← all styles; uses CSS custom properties
    ├── main.py         ← entire Python game logic; SnakeCashRush class + constants
    └── app.js          ← JS bridge only; no game logic
```

- New Python game modules go in `src/` alongside `main.py`.
- Do not add `<script>` blocks with game logic to `index.html`; keep it in `app.js` or `main.py`.
- Do not introduce a package manager, bundler, or transpiler.

---

## Error Handling

- Do not use bare `except:` clauses.
- Catch only the specific exception types you expect and can handle.
- For DOM lookups (`document.getElementById`), validate that the element is not `None`
  before using it if the lookup is outside `__init__` (in `__init__` the DOM is
  guaranteed to be ready by PyScript).
- Do not silently swallow exceptions; at minimum log them with `print()` for
  browser-console visibility.

---

## Testing / Debugging Helpers

Three debug functions are intentionally exposed on `window` for use in browser DevTools:

| JS call | What it does |
|---|---|
| `snakeCashRushSnapshot()` | Returns a JSON string of the full game state |
| `snakeCashRushStep()` | Advances the game by one tick |
| `snakeCashRushPlaceCashAhead()` | Teleports the cash bill in front of the snake |

When writing new features, consider exposing a similar debug hook rather than adding
`print()` statements.
