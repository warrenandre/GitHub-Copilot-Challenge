# Snake Cash Rush

Snake Cash Rush is a web-based Snake game rendered on an HTML canvas, with gameplay logic written in Python and executed in the browser via PyScript.

The game includes:
- Live score tracking
- Persistent best score (stored in browser local storage)
- Increasing game speed as score rises
- Modern arcade-style UI with responsive layout

## Contents

1. Overview
2. Project Structure
3. Requirements
4. Quick Start
5. Gameplay Rules
6. Controls
7. Scoring and Speed
8. Technical Architecture
9. Debug Helpers
10. Troubleshooting
11. Future Improvements

## 1. Overview

Snake Cash Rush runs completely in the browser:
- UI is provided by HTML and CSS.
- Core game loop, movement, collisions, and rendering are implemented in Python.
- A small JavaScript bridge provides browser-specific helpers (animation frame and local storage).

No backend service is required.

## 2. Project Structure

```text
games/snake/
   README.md
   src/
      index.html   # App shell, HUD, canvas, and PyScript includes
      styles.css   # Visual design, layout, animation, and responsive behavior
      main.py      # Core game logic, game loop, rendering, and input handling
      app.js       # Browser bridge (requestAnimationFrame + best score storage)
```

## 3. Requirements

- Python 3.10+
- Modern browser (Edge, Chrome, Firefox)
- Internet access on first load to fetch:
   - PyScript runtime assets
   - Google Fonts

## 4. Quick Start

From the repository root:

```powershell
cd games/snake/src
python -m http.server 8000
```

Open in your browser:

```text
http://localhost:8000/index.html
```

Notes:
- Serve over HTTP. Opening `index.html` directly from disk may break runtime behavior.
- First load can take a few seconds while PyScript initializes.

## 5. Gameplay Rules

- The snake starts near the center of a 20x20 grid.
- Collect cash bills (`$`) to gain score and grow the snake.
- The run ends if the snake hits:
   - A wall
   - Its own body
- After game over, use the restart button or press `R`.

## 6. Controls

- Move Up: `ArrowUp` or `W`
- Move Down: `ArrowDown` or `S`
- Move Left: `ArrowLeft` or `A`
- Move Right: `ArrowRight` or `D`
- Restart: `R`

Behavior details:
- Pressing a movement key on the start screen begins the run.
- Immediate reverse direction is blocked (for example, left to right in one step).

## 7. Scoring and Speed

- Each cash pickup grants `10` points.
- Best score is persisted in `localStorage` under key:
   - `snake-cash-rush-best`

Tick timing (from `main.py` constants):
- Base tick: `160ms`
- Minimum tick: `82ms`
- Speed step: `5ms` faster per pickup tier

The game accelerates gradually as score increases.

## 8. Technical Architecture

### Frontend shell

- `index.html` defines the game card, HUD, canvas, overlay, and status area.
- PyScript is loaded from CDN and executes `main.py` in-browser.

### Python gameplay engine (`main.py`)

The `SnakeCashRush` class handles:
- State lifecycle (`start_game`, `restart_game`, `end_game`)
- Input mapping (`handle_keydown`)
- Frame timing (`game_frame`, `advance`)
- Collision checks (`hit_wall`, body collision logic)
- Score and best-score updates (`sync_best_score`)
- Canvas rendering (`draw_board`, `draw_cash`, `draw_snake`)

Core constants:
- `BOARD_CELLS = 20`
- `BOARD_PIXELS = 560`
- `SCORE_PER_BILL = 10`

### JavaScript bridge (`app.js`)

Exposes `window.snakeCashRushBridge` with:
- `raf(callback)` and `cancelRaf(handle)` for animation scheduling
- `readBestScore()` and `writeBestScore(score)` for persisted best score

## 9. Debug Helpers

For local debugging in browser dev tools, Python registers helper functions on `window`:

- `snakeCashRushSnapshot()`
   - Returns JSON of current game state (running, score, direction, snake, cash, tick).
- `snakeCashRushPlaceCashAhead()`
   - Places cash in a nearby safe tile to speed up manual testing.
- `snakeCashRushStep()`
   - Advances the simulation by one game step.

Example usage in browser console:

```javascript
JSON.parse(window.snakeCashRushSnapshot())
window.snakeCashRushPlaceCashAhead()
window.snakeCashRushStep()
```

## 10. Troubleshooting

### App loads but game does not run

- Verify you are using `http://localhost:8000/index.html`.
- Check browser console for failed network requests to PyScript CDN files.

### Styling looks incomplete

- Confirm internet access (fonts and PyScript CSS are loaded from CDNs).
- Hard refresh the page (`Ctrl+F5`).

### Best score does not persist

- Ensure browser local storage is enabled.
- In private/incognito mode, stored values may reset after the session ends.

### `python` command is not recognized (Windows)

Try:

```powershell
py -m http.server 8000
```

## 11. Future Improvements

- Add touch controls for mobile gameplay.
- Add pause/resume support.
- Add selectable difficulty presets.
- Add sound effects and optional mute toggle.
- Add lightweight automated gameplay checks around state transitions.