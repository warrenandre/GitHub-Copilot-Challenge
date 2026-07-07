# Snake Cash Rush

Snake Cash Rush is a browser arcade game where a snake collects cash bills, speeds up over time, and tracks your best run.

## Run The Game

### Prerequisites

- Python 3.10+
- A modern browser (Edge, Chrome, Firefox)
- Internet access for first load (PyScript and Google Fonts are loaded from CDNs)

### Start locally

1. Open a terminal and go to this folder:

   ```powershell
   cd games/snake
   ```

2. Start a local static server:

   ```powershell
   python -m http.server 8000
   ```

3. Open the game in your browser:

   ```text
   http://localhost:8000/src/
   ```

4. Wait a moment for PyScript to initialize, then click **Start Run**.

## How To Play

- Move with **Arrow Keys** or **W / A / S / D**.
- Collect cash bills to increase your score.
- Each pickup makes the game a little faster.
- Avoid walls and your own body.
- Press **R** to restart at any time.

## Scoring

- Each cash bill gives **+10 points**.
- Your best score is saved in browser local storage and shown in the HUD.

## Project Structure

```text
games/
  snake/
    README.md          # Project documentation
    src/
      index.html       # Game page, HUD, and PyScript wiring
      styles.css       # Visual styling and responsive layout
      main.py          # Core Snake game logic (PyScript/Pyodide)
      app.js           # Browser bridge (RAF + best score persistence)
```

## Troubleshooting

### Game does not start

- Make sure you opened `http://localhost:8000/src/` and not the HTML file directly.
- Check the browser console for blocked or failed PyScript CDN requests.

### Styles or fonts look incorrect

- Confirm internet access for external stylesheet/font resources.
- Refresh once after first load.

### Best score is not saved

- Ensure browser local storage is enabled.
- In private/incognito mode, saved data may be cleared when the session closes.