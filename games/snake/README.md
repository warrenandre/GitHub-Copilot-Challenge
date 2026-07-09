# Snake Cash Rush

Snake Cash Rush is a browser-based Snake game powered by **PyScript** — the game logic is written in Python and runs entirely in the browser via WebAssembly. Collect cash bills, grow your snake, and beat your best score.

---

## Features

- Python game engine running client-side via [PyScript](https://pyscript.net/) (no server required beyond static file serving)
- Smooth `requestAnimationFrame`-driven render loop with variable tick speed — the snake accelerates as your score grows
- Cash-bill pickups worth **+10 points** each, with a burst animation on collection
- Persistent best score stored in `localStorage` — survives page reloads
- Responsive, dark-themed UI built with CSS custom properties and Google Fonts (Space Grotesk + Sora)
- Keyboard support: Arrow keys and WASD

---

## Project Structure

```
games/snake/
├── README.md           ← you are here
└── src/
    ├── index.html      ← app shell, HUD elements, and PyScript config
    ├── styles.css      ← visual design, dark theme, responsive layout
    ├── main.py         ← Python game logic (snake, collision, scoring, rendering)
    └── app.js          ← JS bridge: requestAnimationFrame, localStorage best-score
```

### File responsibilities

| File | Purpose |
|---|---|
| `index.html` | Page skeleton, HUD tiles (Score / Best), canvas element, overlay card, and the `<py-config>` / `<script type="py">` tags that boot PyScript |
| `styles.css` | Full visual layer — dark gradient background, glassmorphism card, score tiles, canvas frame, overlay, and cash-burst animation |
| `main.py` | `SnakeCashRush` class: game state, tick loop, direction handling, collision detection, cash spawning, canvas drawing, and DOM updates |
| `app.js` | `window.snakeCashRushBridge` object exposing `raf()`, `cancelRaf()`, `readBestScore()`, and `writeBestScore()` to the Python layer |

---

## Prerequisites

| Requirement | Details |
|---|---|
| Python 3.10+ | Required only to run the static file server (`python -m http.server`) |
| Modern browser | Chrome 105+, Edge 105+, or Firefox 110+ (WebAssembly required) |
| Internet access | Needed on first load to fetch PyScript (CDN) and Google Fonts |

> **Why a server?** PyScript fetches WASM modules via `fetch()`, which browsers block on `file://` origins due to CORS. A local HTTP server is the simplest fix.

---

## How to Run

1. Open a terminal at the `games/snake` directory:

   ```bash
   cd games/snake
   ```

2. Start a static HTTP server:

   ```bash
   python -m http.server 8000
   ```

3. Open your browser and navigate to:

   ```
   http://localhost:8000/src/
   ```

4. Wait **5–15 seconds** on the first load while PyScript downloads and compiles its WebAssembly runtime. Subsequent loads are faster (cached by the browser).

5. Click **Start Run** or **Play Now**, or just press any arrow key to begin.

---

## How to Play

| Action | Key(s) |
|---|---|
| Steer up | `↑` or `W` |
| Steer down | `↓` or `S` |
| Steer left | `←` or `A` |
| Steer right | `→` or `D` |
| Restart run | `R` |

### Objective

- Guide the snake around the 20×20 grid to collect **cash bills** (💵).
- Each bill collected adds **+10 points** and grows the snake by one segment.
- The snake speeds up as your score increases, capping at a minimum tick interval of **82 ms**.
- The run ends if the snake hits a **wall** or its **own body**.
- Your **best score** is automatically saved and displayed in the HUD.

### Scoring

| Event | Points |
|---|---|
| Collect a cash bill | +10 |

---

## Game Constants (main.py)

| Constant | Value | Description |
|---|---|---|
| `GRID_SIZE` | 20 px | Pixel size of each grid cell |
| `BOARD_CELLS` | 20 | Number of cells per row/column |
| `BOARD_PIXELS` | 560 px | Canvas dimensions |
| `BASE_TICK_MS` | 160 ms | Starting tick interval |
| `MIN_TICK_MS` | 82 ms | Fastest possible tick interval |
| `SPEED_STEP_MS` | 5 ms | Tick reduction per cash bill collected |
| `SCORE_PER_BILL` | 10 | Points awarded per cash bill |

---

## Troubleshooting

### Game does not start / blank canvas

- Ensure you are serving via `http://localhost:8000/src/` — opening `index.html` directly with `file://` will fail.
- Open the browser DevTools console (`F12`) and look for network errors on PyScript or WASM assets.

### Styling looks broken / fonts missing

- Confirm you have internet access for the CDN assets (PyScript stylesheet + Google Fonts).
- Hard-refresh the page (`Ctrl+Shift+R` / `Cmd+Shift+R`) after the first load.

### PyScript takes too long to load

- The initial download (~6 MB of WASM) is normal. Subsequent visits load from the browser cache.
- If on a slow connection, wait up to 30 seconds before the Python runtime boots.

### The best score does not persist

- Confirm local storage is enabled in the browser.
- If you use private browsing, stored values may be cleared when the session ends.

## Development Notes

- The game is intentionally frontend-only.
- Python handles the core gameplay logic.
- JavaScript is limited to browser-specific helpers for animation timing and local storage.