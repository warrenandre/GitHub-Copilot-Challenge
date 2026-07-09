# GitHub Copilot Instructions

## Project Overview
This repository contains the **Snake Cash Rush** game built with Python (Pyodide) and vanilla HTML/CSS/JS.
Copilot should follow the standards below when generating or modifying code in this project.

---

## Project Context

### Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Game logic | Python 3.11+ | Runs entirely in the browser via Pyodide |
| Browser runtime | [Pyodide](https://pyodide.org) | WASM-based CPython — no server required |
| JS/Python bridge | `pyodide.ffi.create_proxy` | Wraps Python callables for JS event listeners |
| Rendering | HTML5 Canvas 2D API | Accessed from Python via `js.document` |
| Styling | Vanilla CSS (no framework) | BEM-inspired class naming, CSS keyframes for animation |
| JS host page | Vanilla JavaScript | Thin bridge layer only — no app logic lives here |
| Package manager | None (no `npm`, no `pip` at runtime) | Pyodide stdlib only; no third-party Python packages |
| Test runner | `pytest` | For pure-logic unit tests run outside the browser |

### Architecture Decisions

#### 1. Python-first game logic
All game state (`snake`, `direction`, `score`, `tick_ms`) lives in the `SnakeCashRush` Python class.
JavaScript is intentionally kept as a **thin bridge** — it only:
- Bootstraps Pyodide and loads `main.py`
- Exposes `window.snakeCashRushBridge` with `readBestScore`, `writeBestScore`, and `raf` (requestAnimationFrame wrapper)
- Forwards no game logic whatsoever

**Why:** Keeps the game fully testable in a standard Python environment without a browser.

#### 2. Fixed-timestep game loop
The game loop uses an **accumulator pattern** (`game_frame` → `accumulator += delta` → drain in `tick_ms` steps).
This decouples game speed from display refresh rate (60 Hz vs 120 Hz monitors).

**Why:** Ensures consistent snake speed regardless of the device's frame rate.

#### 3. Immutable `Point` dataclass
`Point(x, y)` is a `frozen=True` dataclass used for all grid coordinates.
It is hashable by default, enabling O(1) `in` lookups on `set(snake)`.

**Why:** Avoids accidental mutation of coordinates and makes collision checks efficient.

#### 4. JS proxy lifecycle management
Every `create_proxy()` call is stored as an instance attribute (e.g. `self._key_proxy`).
All proxies are explicitly destroyed in `destroy()` to prevent memory leaks in Pyodide.

**Why:** Pyodide proxies hold references on both the Python and JS heaps; failing to destroy them leaks memory on long-running pages.

#### 5. No external Python dependencies
The project deliberately uses only the Python standard library (`dataclasses`, `random`, `typing`, `json`).

**Why:** Pyodide package installs are slow and add network overhead; the game logic is simple enough not to need them.

---

### Preferred Libraries & Tools

#### Python (in-browser via Pyodide)
- ✅ `dataclasses` — for data structures (`Point`)
- ✅ `random.choice` — for cash spawn randomisation
- ✅ `typing` — for type hints (`Iterable`, etc.)
- ✅ `json` — for `snapshot_json` debug output
- ❌ Do **not** add `numpy`, `pygame`, or any package requiring a Pyodide install

#### Python (test environment only)
- ✅ `pytest` — test runner
- ✅ `unittest.mock` — for mocking `document`, `window`, `create_proxy`
- ❌ Do **not** use `pytest-asyncio` unless async game logic is introduced

#### JavaScript / Browser
- ✅ Vanilla JS only — no frameworks, no bundlers
- ✅ Native CSS animations (`@keyframes`) — no animation libraries
- ❌ Do **not** introduce `React`, `Vue`, `jQuery`, or any JS framework
- ❌ Do **not** add a `package.json` or `node_modules`

---

### Project Structure

```
GitHub-Copilot-Challenge/
├── .github/
│   └── copilot-instructions.md   # ← this file
├── games/
│   └── snake/
│       ├── src/
│       │   └── main.py           # All Python game logic
│       ├── index.html            # Host page — bootstraps Pyodide
│       ├── style.css             # Game styling
│       └── bridge.js             # Thin JS bridge (localStorage, rAF)
└── tests/
    └── test_main.py              # Unit tests for pure logic methods
```

---

## Naming Conventions

### Python
- **Classes**: `PascalCase` — e.g. `SnakeCashRush`, `Point`
- **Methods & functions**: `snake_case` — e.g. `reset_state`, `spawn_cash`
- **Variables**: `snake_case` — e.g. `tick_ms`, `next_head`
- **Constants**: `UPPER_SNAKE_CASE` — e.g. `BOARD_CELLS`, `BASE_TICK_MS`
- **Private/internal helpers**: prefix with underscore — e.g. `_key_proxy`, `_frame_proxy`
- **Boolean flags**: use descriptive prefixes — `is_`, `has_`, `will_` — e.g. `will_collect`, `is_reverse`

### JavaScript / HTML
- **Variables & functions**: `camelCase` — e.g. `readBestScore`, `writeBestScore`
- **HTML element IDs**: `camelCase` — e.g. `gameCanvas`, `scoreValue`, `cashBurst`
- **CSS classes**: `kebab-case` — e.g. `game-overlay`, `cash-burst`, `pulse`

---

## Error Handling Patterns

- **Never silently swallow exceptions.** Always log or surface errors meaningfully.
- **Guard early with `return`** rather than deeply nested `if` blocks.
- **Provide safe fallbacks** for unreachable-but-possible states, e.g.:
  ```python
  # Fallback when board is completely full — unreachable in normal play
  return choice(available) if available else Point(0, 0)
  ```
- **Validate external input** (e.g. keyboard events, JS bridge values) before use.
- **Pyodide/JS boundary calls** (`window.*`, `document.*`) should be isolated in dedicated methods so failures are easy to locate and mock in tests.
- Use `int()`, `float()`, `str()` coercions explicitly when receiving values from the JS bridge — do not assume types.

---

## Documentation Expectations

### Inline Comments
- Add inline comments to explain the **"why"**, not the "what".
- Complex logic sections **must** have a comment explaining the reasoning, e.g.:
  ```python
  # Reject 180-degree reversals — moving into the snake's own neck would
  # cause an immediate and unfair self-collision on the very next tick.
  ```
- Avoid restating the code in plain English — comments should add context.

### Docstrings
- All **public methods** should have a one-line docstring unless the method name is fully self-explanatory.
- Use plain sentences, no need for NumPy/Google style unless the method has complex args:
  ```python
  def spawn_cash(self, snake: Iterable[Point]) -> Point:
      """Return a random unoccupied cell for the next cash bill."""
  ```

### Constants
- Every module-level constant must have a trailing comment explaining its purpose:
  ```python
  BASE_TICK_MS = 160   # Starting game loop interval in milliseconds
  MIN_TICK_MS  = 82    # Fastest allowed tick — below this the game is unplayable
  SPEED_STEP_MS = 5    # Tick reduction per collected bill (increases difficulty)
  ```

---

## Code Style

- **Type hints are required** on all function signatures.
- **`dataclasses`** should be used for simple data-holding structures (e.g. `Point`).
- **Immutable data** should use `frozen=True` on dataclasses where possible.
- Keep methods **focused and short** — if a method exceeds ~30 lines, consider splitting it.
- Avoid inline lambdas with side effects; extract them into named methods where readability suffers.
- All Pyodide proxy objects (`create_proxy`) must be stored as instance attributes so they can be properly destroyed in `destroy()`.

---

## Testing Expectations

- Pure logic methods (`hit_wall`, `is_reverse`, `spawn_cash`, `advance`) should have unit tests.
- Tests should be placed in a `/tests` directory at the project root.
- Test file naming: `test_<module>.py` — e.g. `test_main.py`
- Use `pytest` as the test runner.
- Mock all JS/DOM dependencies (`document`, `window`, `create_proxy`) in tests.

---

## Commit Message Convention

Follow **Conventional Commits**:

```
<type>: <short description>
```

| Type       | Use for                               |
|------------|---------------------------------------|
| `feat`     | New feature                           |
| `fix`      | Bug fix                               |
| `docs`     | Documentation / comments only         |
| `style`    | Formatting, no logic change           |
| `refactor` | Code restructure, no behaviour change |
| `test`     | Adding or updating tests              |
| `chore`    | Build, config, dependency changes     |

**Example:**
```
docs: add inline comments explaining complex logic in snake game
feat: increase speed cap per collected bill
fix: prevent 180-degree reversal on rapid key presses
```