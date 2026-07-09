# Snake Cash Rush

Snake Cash Rush is a browser game inspired by classic Snake, rebuilt with a finance arcade theme. It combines a modern, animated UI with Python gameplay logic running in-browser through PyScript.

## Highlights

- Python game engine in the browser (PyScript + Pyodide)
- Responsive canvas board with styled overlays and HUD
- Score and best-score tracking
- Persistent best score via localStorage
- Dynamic difficulty that speeds up as score increases
- Built-in debug/testing hooks exposed on `window`

## Tech Stack

- HTML/CSS for layout, visual style, and animation
- JavaScript for browser bridge utilities
- Python for game rules, rendering logic, and input handling
- PyScript runtime loaded from CDN

## Directory Structure

```text
games/snake/
   README.md
   src/
      index.html   # UI shell, HUD, canvas, overlays, and PyScript bootstrapping
      styles.css   # Theme, layout, responsive behavior, and animations
      app.js       # requestAnimationFrame + localStorage bridge
      main.py      # Core game logic and canvas rendering
```

## Requirements

- Python 3.10+
- A modern browser (Edge, Chrome, Firefox)
- Internet access on first load for:
   - PyScript assets
   - Google Fonts used by the UI

## Quick Start

### Option A: Serve from `games/snake/src` (recommended for this workspace)

1. Open terminal in `games/snake/src`.
2. Start a local HTTP server:

```powershell
python -m http.server 8000
```

3. Open:

```text
http://localhost:8000/index.html
```

### Option B: Serve from `games/snake`

1. Open terminal in `games/snake`.
2. Start the server:

```powershell
python -m http.server 8000
```

3. Open:

```text
http://localhost:8000/src/
```

## Gameplay

### Objective

Collect cash bills, grow your snake, and set the highest score before colliding with a wall or your own body.

### Controls

- Move: `Arrow Keys` or `W A S D`
- Restart immediately: `R`
- Start/Restart with mouse: `Start Run` or overlay action button

### Rules

- The snake cannot reverse direction directly (180-degree turn prevention).
- Each cash pickup increases score by 10.
- On pickup, the snake grows by one segment.
- A run ends on wall collision or self-collision.

## Scoring and Speed Model

- Score per bill: `10`
- Base tick interval: `160ms`
- Minimum tick interval: `82ms`
- Speed-up per bill collected: `5ms`

Effective tick formula:

```text
tickMs = max(82, 160 - billsCollected * 5)
```

Where:

```text
billsCollected = score / 10
```

This means gameplay accelerates steadily as your score rises.

## UI and UX Notes

- Hero panel introduces the run theme and status
- HUD displays current score and persisted best score
- Overlay presents start and game-over states
- Cash burst animation appears on successful pickup
- Score tiles pulse to emphasize score and best-score updates
- Mobile-friendly layout via responsive breakpoints

## Persistence

Best score is stored in browser localStorage under:

```text
snake-cash-rush-best
```

Clearing site data or using private mode may reset this value.

## Architecture Overview

### `main.py`

- Owns game state (snake, direction, score, speed, cash position)
- Handles keyboard input and state transitions
- Runs frame loop via `requestAnimationFrame` through JS bridge
- Renders board, snake, and cash directly on canvas
- Updates DOM HUD/overlay state

### `app.js`

- Exposes `window.snakeCashRushBridge` with:
   - `raf(callback)`
   - `cancelRaf(handle)`
   - `readBestScore()`
   - `writeBestScore(score)`

### `index.html`

- Loads visual assets and PyScript runtime
- Defines game UI elements and canvas
- Boots Python via:

```html
<script type="py" src="main.py"></script>
```

## Debug/Test Hooks

For local debugging from browser DevTools, `main.py` exposes:

- `window.snakeCashRushSnapshot()`
   - Returns JSON snapshot of state (score, direction, snake, cash, tick speed, flags)
- `window.snakeCashRushPlaceCashAhead()`
   - Moves cash to a valid nearby tile for faster manual testing
- `window.snakeCashRushStep()`
   - Advances one simulation step (useful for controlled verification)

## Troubleshooting

### Blank page or Python not initializing

- Ensure the page is loaded over HTTP, not opened directly from file explorer.
- Confirm PyScript CDN URLs are reachable from your network.
- Check browser console for blocked or failed CDN requests.

### Controls do not respond

- Click the game area once to ensure focus.
- Start the run using `Start Run` if still in waiting mode.

### Styling appears broken

- Verify internet access for external fonts and PyScript CSS.
- Hard refresh the page (`Ctrl+F5`).

### Best score not saving

- Verify browser storage is enabled.
- Avoid private/incognito mode if persistent score is expected.

## Development Tips

- Keep game constants centralized in `main.py` (`BASE_TICK_MS`, `SPEED_STEP_MS`, etc.).
- When adjusting visuals, test both desktop and mobile widths.
- Prefer adding behavior in Python first; keep JavaScript bridge minimal and browser-specific.

## Future Enhancements

- Sound effects and music toggle
- Pause/resume support
- Difficulty presets
- Obstacles or timed bonus pickups
- Leaderboard backed by a lightweight API