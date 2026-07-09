# Snake Cash Rush

A browser-based arcade game where you steer a growing snake across a 20×20 grid, collecting cash bills to rack up points while dodging walls and your own tail. The game logic is written in Python and runs entirely in the browser via [PyScript](https://pyscript.net/) — no server required beyond a simple static file host.

---

## Project Structure

```
games/snake/
├── README.md          # This file
└── src/
    ├── index.html     # App shell: canvas, HUD, overlay, and PyScript bootstrap
    ├── styles.css     # Dark finance-themed UI with CSS custom properties and animations
    ├── main.py        # All game logic (Python): state machine, physics, rendering
    └── app.js         # Thin JS bridge exposing requestAnimationFrame and localStorage to Python
```

### Why this split?

Python (via PyScript/Pyodide) cannot directly call browser APIs like `requestAnimationFrame` or `localStorage`. `app.js` exposes these as a small bridge object (`window.snakeCashRushBridge`) so `main.py` can drive the game loop and persist the best score without any Python-to-JS friction.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Modern browser | Chrome 110+, Edge 110+, Firefox 115+, or Safari 17+ |
| Internet access (first load) | PyScript runtime (~8 MB), Google Fonts, and the PyScript stylesheet are fetched from CDN on first visit and then cached |
| Python 3.10+ (local) | Only needed to run the static file server; not required by the game itself |

> **Note:** The game will **not** work when opened directly as a `file://` URL because browsers block cross-origin requests needed by PyScript. Always serve it over HTTP.

---

## Running the Game

1. Open a terminal in the `games/snake` directory:

   ```powershell
   cd games/snake
   ```

2. Start a local static file server:

   ```powershell
   python -m http.server 8000
   ```

3. Open your browser and navigate to:

   ```
   http://localhost:8000/src/
   ```

4. Wait a few seconds for the PyScript runtime to initialise (a loading indicator may briefly appear).

5. Click **Start Run** or press any arrow key to begin.

---

## How to Play

| Action | Keys |
|---|---|
| Steer the snake | `↑ ↓ ← →` or `W A S D` |
| Restart at any time | `R` |
| Start / restart (mouse) | **Start Run** button or **Play Now** / **Run It Back** on the overlay |

### Objective

- Eat the green cash bills to grow the snake and increase your score.
- Each bill collected is worth **$10**.
- Active **Double Points** power-up makes each bill worth **$20** while it lasts.
- The snake speeds up every time you collect a bill — pace increases until the minimum tick interval of **82 ms** is reached.
- The run ends when the snake hits a wall or its own body.
- Your best score is saved in browser `localStorage` and shown in the HUD between sessions.

### Power-Ups

- Power-up pickups can spawn after collecting cash bills.
- **Speed Boost**: temporarily increases movement speed.
- **Invincibility**: temporarily prevents death from walls and self-collision (wall contact wraps to the opposite side).
- **Double Points**: temporarily doubles cash bill value.
- Only one effect is active at a time, and the current effect is shown in the HUD.

---

## Game Mechanics

| Constant | Value | Purpose |
|---|---|---|
| `BOARD_CELLS` | 20 | Grid dimensions (20 × 20 cells) |
| `BOARD_PIXELS` | 560 px | Canvas render size |
| `BASE_TICK_MS` | 160 ms | Starting speed (one step every 160 ms) |
| `MIN_TICK_MS` | 82 ms | Fastest possible speed |
| `SPEED_STEP_MS` | 5 ms | Speed increase per bill collected |
| `SCORE_PER_BILL` | 10 | Points awarded per cash bill |

The game loop uses a **fixed-timestep accumulator** driven by `requestAnimationFrame`. This decouples rendering from game logic so the snake moves at a consistent speed regardless of monitor refresh rate.

---

## Troubleshooting

**The page opens but the game does not start**
- Ensure you are accessing the app via `http://localhost:8000/src/` and not a `file://` URL.
- Open browser DevTools → Console and check for failed network requests to PyScript assets.
- On a slow connection, allow extra time for the Pyodide WASM runtime to download.

**The board is visible but styling looks off**
- Confirm you have internet access; the Google Fonts stylesheet and PyScript core CSS are loaded from CDN.
- Hard-refresh the page (`Ctrl + Shift + R`) to clear any partial cache.

**The best score does not persist between sessions**
- Check that `localStorage` is not blocked (some privacy extensions or browser settings disable it).
- In private/incognito mode, `localStorage` is cleared when the window is closed — scores will not carry over.

---

## Development Notes

- **No build step.** The project is intentionally zero-config: edit a file, refresh the browser.
- **Python-first game logic.** All state, collision detection, spawning, and rendering live in `main.py`. JavaScript is kept to the absolute minimum.
- **Canvas rendering.** The snake and cash bill are drawn directly onto an HTML5 `<canvas>` element from Python using the 2D context API exposed by Pyodide.
- **Debug hooks.** Three functions are exposed on `window` for console-based debugging:
  - `snakeCashRushSnapshot()` — returns a JSON snapshot of the current game state.
  - `snakeCashRushPlaceCashAhead()` — teleports the cash bill one cell ahead of the snake head.
  - `snakeCashRushStep()` — advances the game by a single tick.