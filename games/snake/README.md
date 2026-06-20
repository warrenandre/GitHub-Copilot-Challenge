# Snake Cash Rush

Snake Cash Rush is a browser-based Snake game with Python game logic, cash-bill pickups, a sleek modern UI, live score tracking, and a persisted best score.

## Project Layout

- `src/index.html`: app shell and HUD
- `src/styles.css`: visual design and responsive layout
- `src/main.py`: Python game logic running in the browser
- `src/app.js`: small browser bridge for animation timing and best-score storage

## Prerequisites

- Python 3.10 or later installed locally
- A modern browser such as Microsoft Edge or Chrome
- Internet access the first time the app loads, because PyScript and Google Fonts are fetched from their CDNs

## Getting Started

1. Open a terminal in `games/snake`.
2. Start a simple static server:

   ```powershell
   python -m http.server 8000
   ```

3. In your browser, open `http://localhost:8000/src/`.
4. Wait a few seconds for the PyScript runtime to initialize.
5. Click `Start Run` or press an arrow key to begin.

## How To Play

- Use `Arrow Keys` or `W`, `A`, `S`, `D` to steer the snake.
- Eat the money bills to grow and increase your score.
- Avoid crashing into walls or your own snake body.
- Press `R` at any time to restart the run.
- Your best score is stored in the browser and shown in the HUD.

## Troubleshooting

### The page opens but the game does not start

- Make sure you opened the app through `http://localhost:8000/src/` and not by double-clicking the HTML file.
- Open the browser developer console and check for failed network requests to PyScript assets.

### The board shows but styling looks broken

- Confirm you have internet access for the external font and PyScript stylesheet downloads.
- Refresh the page once after the first load.

### The best score does not persist

- Confirm local storage is enabled in the browser.
- If you use private browsing, stored values may be cleared when the session ends.

## Development Notes

- The game is intentionally frontend-only.
- Python handles the core gameplay logic.
- JavaScript is limited to browser-specific helpers for animation timing and local storage.