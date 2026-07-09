# Snake Cash Rush

Snake Cash Rush is a browser-based arcade game inspired by classic Snake, built with Python game logic running in the browser through PyScript.

The game blends a modern finance-themed UI with fast gameplay loops:
- collect cash bills to score and grow
- survive collisions with walls and yourself
- accelerate progressively as your score rises
- track and persist your local best score

## Demo Experience

- Modern single-page game UI with animated overlay states
- 20x20 board rendered on HTML canvas
- Keyboard-first controls (arrows + WASD)
- Responsive layout for desktop and mobile screens

## Features

- **Python gameplay in browser** via PyScript (no backend required)
- **Smooth animation timing** using `requestAnimationFrame`
- **Progressive difficulty** with dynamic tick-rate acceleration
- **Persistent best score** via browser local storage
- **Game states**: ready, running, crash/game-over, restart
- **HUD feedback** with score pulse and cash burst effects
- **Debug helper hooks** exposed to `window` for quick testing

## Tech Stack

- **Runtime:** Browser + PyScript (`2025.3.1` from CDN)
- **Logic:** Python (`src/main.py`)
- **Rendering:** HTML5 Canvas
- **UI:** HTML + CSS
- **Bridge:** JavaScript (`src/app.js`) for browser APIs (animation + storage)

## Project Structure

```text
games/snake/
   README.md
   src/
      index.html   # app shell, HUD, overlay, and script wiring
      styles.css   # visual theme, animation, responsive behavior
      main.py      # game loop, input handling, collision, rendering
      app.js       # browser bridge (RAF + localStorage)
```

## Gameplay Rules

1. The snake starts centered on a 20x20 grid.
2. Eat the cash bill (`$`) to gain points and grow.
3. Each pickup increases score by `10`.
4. Crashing into walls or your body ends the run.
5. Press restart and try to beat your best score.

### Difficulty Scaling

Game speed is controlled by a tick interval in milliseconds:

$$
tickMs = \max(82,\ 160 - 5 \times \frac{score}{10})
$$

This means each cash pickup reduces tick time by `5ms` until a minimum of `82ms`.

## Controls

- `Arrow Keys` or `W / A / S / D`: move snake
- `R`: restart immediately
- `Start Run` button: start or restart run from UI

## Prerequisites

- Python `3.10+`
- A modern browser (Edge, Chrome, Firefox)
- Internet access on load (PyScript + Google Fonts are fetched from CDNs)

## Quick Start

1. Open a terminal in `games/snake`.
2. Start a local static server:

```powershell
python -m http.server 8000
```

3. Open the app:

```text
http://localhost:8000/src/
```

4. Wait for PyScript to initialize, then press **Start Run**.

## How It Works

### 1) Python Game Engine (`src/main.py`)

- Maintains state: snake body, direction, cash position, score, best score, game flags
- Drives frame updates and fixed-step progression (`accumulator` + `tickMs`)
- Handles keyboard input and direction constraints (prevents direct reverse movement)
- Detects collisions and transitions to game-over state
- Draws board, snake, and cash each frame on canvas

### 2) JavaScript Bridge (`src/app.js`)

Defines `window.snakeCashRushBridge`:
- `raf(callback)` and `cancelRaf(handle)`
- `readBestScore()` and `writeBestScore(score)` using local storage key:
   - `snake-cash-rush-best`

### 3) UI Layer (`src/index.html`, `src/styles.css`)

- HUD values (`Score`, `Best`) bound by DOM updates from Python
- Overlay messaging for ready and game-over states
- Animated cash burst and pulse effects for feedback

## Debug/Test Helpers

The game exposes utility functions on `window` for quick manual testing:

- `snakeCashRushSnapshot()` -> returns a JSON state snapshot string
- `snakeCashRushPlaceCashAhead()` -> places cash in front of the snake when possible
- `snakeCashRushStep()` -> advances one game step (debug mode)

Example usage from browser DevTools console:

```javascript
JSON.parse(window.snakeCashRushSnapshot());
window.snakeCashRushPlaceCashAhead();
window.snakeCashRushStep();
```

## Troubleshooting

### Game does not start

- Ensure you opened the app through `http://localhost:8000/src/` (not direct file open).
- Check DevTools Console/Network for failed PyScript CDN requests.

### Styling looks incorrect or incomplete

- Confirm internet access for Google Fonts and PyScript assets.
- Hard refresh once after first load.

### Best score is not retained

- Verify local storage is enabled in browser settings.
- Private/incognito sessions may clear storage on close.

## Performance Notes

- Canvas size is `560x560` with a logical `20x20` board.
- Animation is browser-synced with `requestAnimationFrame`.
- Gameplay speed is fixed-step to keep movement consistent across devices.

## Extending the Game

Ideas for enhancements:
- add pause/resume state
- add sound effects for pickups and collision
- add obstacle tiles or bonus pickups
- add touch controls for mobile play
- add selectable difficulty presets

## License

This project is part of the GitHub Copilot challenge workspace. Add your preferred license if you plan to distribute it publicly.