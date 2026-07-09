# Snake Cash Rush

Snake Cash Rush is a browser-based Snake game with Python-driven game logic, cash-bill pickups, a sleek modern UI, live score tracking, and a persisted best score. It runs entirely in the browser — no backend, no build step, and no additional dependencies beyond a static file server.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Getting Started](#getting-started)
6. [How to Play](#how-to-play)
7. [Gameplay Features](#gameplay-features)
8. [Architecture Notes](#architecture-notes)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The player steers a snake around a 20×20 grid, collecting money-bill pickups to grow the snake and increase their score. The game ends on wall or self-collision. A best score is persisted in browser `localStorage` and survives page reloads. Speed increases gradually as the score climbs, keeping each run progressively more challenging.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Game logic | Python 3 via [PyScript](https://pyscript.net) | State management, loop, collision, scoring |
| Rendering | HTML5 Canvas | Board drawing and pickup animation |
| UI / HUD | HTML + CSS | Score panel, overlays, responsive layout |
| Browser bridge | JavaScript (`app.js`) | Animation timing, `localStorage` access |
| Fonts | Google Fonts (Space Grotesk, Sora) | Visual identity |

> PyScript downloads its runtime from its CDN on first load. An internet connection is required for that initial fetch; subsequent runs use the browser cache.

---

## Project Structure

```
games/snake/
├── README.md          ← this file
└── src/
    ├── index.html     ← application shell, HUD markup, and PyScript bootstrap
    ├── styles.css     ← full visual system, layout, animations, and responsive rules
    ├── main.py        ← Python game class: state, loop, input, rendering, scoring
    └── app.js         ← JS bridge: requestAnimationFrame driver and localStorage helpers
```

### File Responsibilities

**`index.html`**
Declares the page structure: background orbs, hero strip, HUD panel (score, best score, start button), canvas board frame with overlay card, and the controls footer. Loads PyScript, the CSS, and `app.js`. The `<script type="py" src="main.py">` tag boots the Python runtime at page load.

**`styles.css`**
Implements the dark glass visual system with emerald accents and soft glow effects. Controls layout behaviour for the game card, HUD tiles, board frame, overlay cards, and cash-burst animation. Includes a responsive breakpoint that stacks and scales elements for narrow mobile viewports.

**`main.py`**
Contains the `SnakeCashRush` class — the single source of truth for all gameplay logic:
- `reset_state()` — sets initial snake position, direction, score, and tick speed
- `start_game()` / `restart_game()` — run lifecycle management
- `game_frame()` — fixed-timestep loop driven by `requestAnimationFrame` timestamps
- `step()` — advances the snake, handles pickup collection, collision detection, and speed ramping
- `draw()` — renders the board, snake, and money-bill pickup to the canvas each frame
- `handle_keydown()` — maps arrow keys and WASD to direction changes; rejects illegal reversal; maps `R` to restart

**`app.js`**
Exposes a `window.snakeCashRushBridge` object with `readBestScore()` and `writeBestScore()` helpers that wrap `localStorage`, plus a `requestAnimationFrame` shim used by the Python frame loop. Runs synchronously before PyScript initialises.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.10+** | Only needed to run the static file server |
| **Modern browser** | Chrome 110+, Edge 110+, or Firefox 115+ recommended |
| **Internet access** | Required on first load for PyScript CDN and Google Fonts; cached afterwards |

---

## Getting Started

### 1. Clone or open the repository

```bash
# If you have not cloned the repo yet:
git clone <repo-url>
cd GitHub-Copilot-Challenge
```

### 2. Navigate to the game directory

```bash
cd games/snake
```

### 3. Start a local static server

**Python (recommended):**
```bash
python -m http.server 8000
```

**Node.js alternative (if Python is unavailable):**
```bash
npx serve . -p 8000
```

### 4. Open the game in your browser

```
http://localhost:8000/src/
```

> Do **not** open `index.html` by double-clicking. PyScript requires files to be served over HTTP — a `file://` origin will block the runtime from loading.

### 5. Wait for PyScript to initialise

On first load the browser downloads the PyScript runtime (~5 MB). A brief loading indicator appears in the overlay. Subsequent loads are served from cache and are near-instant.

### 6. Start playing

Click **Start Run** or press any arrow key.

---

## How to Play

| Action | Input |
|---|---|
| Steer up | `↑` or `W` |
| Steer down | `↓` or `S` |
| Steer left | `←` or `A` |
| Steer right | `→` or `D` |
| Restart run | `R` or click **Start Run** |

**Objective:** Collect as many money bills as possible without hitting a wall or your own snake body.

**Scoring:** Each money bill collected adds **10 points** to your current score. Your best score is saved in the browser automatically and displayed in the HUD.

---

## Gameplay Features

- **Cash-bill pickups** — styled money-bill icons replace the standard pellet, reinforcing the finance theme.
- **Progressive speed** — the snake accelerates with each bill collected (from 160 ms/tick down to a floor of 82 ms/tick), making later runs more demanding.
- **Score pulse** — the score tile flashes on each pickup to give immediate visual feedback.
- **Cash burst animation** — a `+$` burst appears at the pickup location when a bill is collected.
- **Persisted best score** — stored in `localStorage`; survives page reloads and browser restarts.
- **Overlay states** — distinct overlay cards communicate the ready, active, and game-over states clearly.
- **Responsive layout** — the game card stacks and scales on narrow viewports (tested at 390 × 844 px).
- **Illegal reversal prevention** — the snake cannot reverse direction into itself; the input is silently discarded.

---

## Architecture Notes

### Why Python in the browser?

PyScript compiles CPython to WebAssembly and runs it inside the browser sandbox. This allows the game logic to be written in idiomatic Python (dataclasses, type hints, standard library) without a separate backend or transpilation step.

### Fixed-timestep game loop

`app.js` calls `requestAnimationFrame` and forwards each timestamp into the Python runtime. `game_frame()` accumulates elapsed time and only advances the game state when the accumulated time exceeds the current tick interval. The board and HUD are re-rendered every frame regardless, keeping animations smooth even between ticks.

### Separation of concerns

JavaScript is intentionally minimal: it owns only browser APIs that PyScript cannot access directly (`localStorage`, `requestAnimationFrame` scheduling). All game rules live in Python. This boundary makes the Python logic independently testable and keeps the JS surface small.

---

## Troubleshooting

### The page opens but the game does not respond

- Confirm the URL is `http://localhost:8000/src/` and not a `file://` path.
- Open the browser developer console (F12) and check the **Console** and **Network** tabs for failed requests to `pyscript.net`.
- If PyScript assets time out, check your internet connection and reload.

### The overlay appears but the board is blank

- The canvas renders after Python initialises. Wait 3–5 seconds on a slow connection.
- If the board remains blank after 10 seconds, check the console for Python exceptions.

### Styling looks unstyled or broken

- Google Fonts is loaded from an external CDN. Confirm network access is available.
- Hard-refresh the page (`Ctrl+Shift+R` / `Cmd+Shift+R`) to bypass a stale cache.

### The game runs but the best score resets every time

- The best score relies on `localStorage`. Confirm your browser does not clear storage on close (private/incognito mode clears `localStorage` at session end).

### Python import errors in the console

- Verify you are running the server from the `games/snake` directory, not from `games/snake/src`.
- Ensure `main.py` and `index.html` are in the same `src/` folder.


### The best score does not persist

- Confirm local storage is enabled in the browser.
- If you use private browsing, stored values may be cleared when the session ends.

## Development Notes

- The game is intentionally frontend-only.
- Python handles the core gameplay logic.
- JavaScript is limited to browser-specific helpers for animation timing and local storage.