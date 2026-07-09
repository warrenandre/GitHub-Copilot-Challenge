# Snake Cash Rush

Snake Cash Rush is a browser-based Snake game with Python-driven gameplay logic (via PyScript), cash pickups, increasing speed, and persistent best-score tracking.

## How To Run

### Prerequisites

- Python 3.10+
- A modern browser (Edge, Chrome, Firefox)
- Internet access on first load (PyScript and font assets are loaded from CDNs)

### Start Locally

1. Open a terminal in `games/snake`.
2. Run a local static server:

```powershell
python -m http.server 8000
```

3. Open `http://localhost:8000/src/` in your browser.
4. Wait for PyScript to initialize.
5. Click `Start Run` (or press a movement key) to begin.

## How To Play

- Goal: collect as many cash bills as possible without crashing.
- Movement: use `Arrow Keys` or `W`, `A`, `S`, `D`.
- Scoring: each cash bill adds points and increases game pace.
- Lose condition: hitting a wall or your own snake body ends the run.
- Restart: press `R` or use the restart button.
- Best score: stored in browser local storage and displayed in the HUD.

## Controls

| Action | Keys |
|---|---|
| Move up | `ArrowUp` / `W` |
| Move down | `ArrowDown` / `S` |
| Move left | `ArrowLeft` / `A` |
| Move right | `ArrowRight` / `D` |
| Restart run | `R` |

## Project Structure

```text
games/snake/
   README.md        # Project documentation
   src/
      index.html     # Page layout, HUD, and canvas container
      styles.css     # Visual styling and responsive behavior
      app.js         # Browser bridge (RAF + local storage helpers)
      main.py        # Core Snake game logic written in Python
```

## Troubleshooting

### Game does not start

- Confirm you opened `http://localhost:8000/src/` and not the file directly from disk.
- Check browser DevTools for failed PyScript asset requests.

### Styling or fonts look off

- Confirm internet access for CDN assets.
- Refresh once after the first load.

### Best score is not saved

- Ensure browser local storage is enabled.
- In private/incognito mode, local storage may be cleared after the session.