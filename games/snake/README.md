# Snake Cash Rush 💰🐍

A modern, browser-based Snake game with Python-powered game logic, cash pickups, live score tracking, and persistent best-score storage. Chase stacks, build momentum, and beat your best run!

## Overview

Snake Cash Rush combines the classic snake game mechanics with a sleek, modern financial theme. Powered by PyScript, this game runs Python directly in the browser, delivering smooth gameplay with responsive controls and engaging visuals.

## Project Structure

```
games/snake/
├── README.md                 # This file
├── src/
│   ├── index.html           # HTML shell, HUD layout, game canvas, and overlays
│   ├── styles.css           # Modern design, responsive layout, animations
│   ├── main.py              # Core game logic (written in Python, runs via PyScript)
│   └── app.js               # Browser bridge for animation timing and score persistence
```

### File Descriptions

- **index.html**: Contains the app shell with the game canvas, score display, start button, and game-over overlay. Uses semantic HTML with accessible ARIA attributes.
- **styles.css**: Provides modern styling with custom fonts (Space Grotesk, Sora), gradient backgrounds, smooth animations, and responsive layout for all screen sizes.
- **main.py**: Implements the complete game logic including snake movement, collision detection, cash spawning, score calculation, and difficulty progression. Communicates with JavaScript for UI updates and event handling.
- **app.js**: A small JavaScript bridge that handles animation frame timing, best-score persistence via browser localStorage, and keyboard event coordination.

## Prerequisites

- **Python 3.10 or later** installed on your system
- **A modern browser** (Chrome, Edge, Firefox, or Safari)
- **Internet access** on first load (PyScript runtime and Google Fonts are fetched from CDNs)

## Getting Started

### Step 1: Navigate to the game directory

```bash
cd games/snake
```

### Step 2: Start a local web server

```bash
python -m http.server 8000
```

You should see output like:
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

### Step 3: Open the game in your browser

Open your browser and navigate to:
```
http://localhost:8000/src/
```

### Step 4: Wait for PyScript to initialize

The first load takes a few seconds as PyScript downloads and initializes the Python runtime. You'll see the game overlay appear once ready.

### Step 5: Start playing

Click **"Play Now"** or press any arrow key to begin your run!

## How To Play

### Controls

- **Arrow Keys** or **WASD** to steer the snake
  - ↑ / W = Move up
  - ↓ / S = Move down
  - ← / A = Move left
  - → / D = Move right

### Gameplay

1. **Collect Cash Bills**: Eat the green $ bills to grow your snake and increase your score
2. **Avoid Obstacles**: Don't crash into the game board walls or your own snake body
3. **Progressive Difficulty**: As you collect bills, the game speeds up, making it progressively harder
4. **Scoring**: Each bill collected grants +10 points
5. **Best Score**: Your highest score is automatically saved in your browser

### Actions

- **R** or click **"Play Again"** after game over to restart
- **Click the "Start Run" button** to begin a new game from the menu

## Gameplay Mechanics

### Snake Movement

- The snake moves in a grid-based environment (20×20 cells)
- Each movement occupies one game tick
- The snake grows by one segment when eating a cash bill
- Game over occurs on collision with walls or the snake's own body

### Cash Spawning

- Cash bills spawn at random positions on the grid
- They avoid the snake's current body segments
- Each collected bill increases your score by 10 points

### Difficulty Progression

- **Base speed**: 160ms per tick
- **Speed increases**: Each bill collected reduces the tick interval by 5ms
- **Maximum speed**: 82ms per tick (nearly 2x faster than base)
- Progressive difficulty keeps the game challenging and exciting

### Score System

- **Points per bill**: 10
- **Best score**: Persists across browser sessions using localStorage
- **Display**: Real-time score shown in the HUD during gameplay

## Troubleshooting

### The page opens but the game does not start

**Issue**: The PyScript runtime hasn't initialized or failed to load.

**Solutions**:
- Ensure you accessed the game via `http://localhost:8000/src/` and not by double-clicking the HTML file
- Open the browser developer console (F12) and check the Console tab for errors
- Check the Network tab for any failed requests to PyScript or Google Fonts
- Try refreshing the page after waiting 10 seconds for the runtime to load

### The board shows but styling looks broken

**Issue**: External CSS resources (fonts, PyScript styles) haven't loaded.

**Solutions**:
- Verify you have internet access
- Refresh the page to retry CDN requests
- Clear your browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete) and reload
- Try a different browser to rule out browser-specific issues

### The snake doesn't respond to keyboard input

**Issue**: Keyboard events aren't being captured properly.

**Solutions**:
- Click on the game canvas to ensure the page has focus
- Try using arrow keys first; if that doesn't work, try WASD keys
- Check the browser console for JavaScript errors
- Restart the game by pressing R or clicking "Play Again"

### The game runs slowly or freezes

**Issue**: Poor performance due to system load or browser issues.

**Solutions**:
- Close other browser tabs to free up memory
- Restart the browser
- Try a different browser (Chrome or Edge typically perform best)
- Check Task Manager (Windows) or Activity Monitor (macOS) for system resource usage

### The best score does not persist

**Issue**: Best score isn't being saved across sessions.

**Solutions**:
- Confirm local storage is enabled in the browser (check browser settings)
- If using private/incognito browsing, stored values are cleared when the session ends
- Check the browser console for any localStorage errors

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Game Logic**: Python 3.10+ (via PyScript)
- **Runtime**: PyScript 2025.3.1 (browser-based Python)
- **Fonts**: Google Fonts (Space Grotesk, Sora)
- **Architecture**: Event-driven with fixed-timestep game loop

## Performance Notes

- **PyScript Runtime**: ~2-3 seconds to initialize on first load
- **Game Loop**: Fixed 60 FPS animation frames with variable game tick speeds
- **Memory**: ~30-50MB after initialization (PyScript runtime overhead)
- **Browser Compatibility**: Works best in Chromium-based browsers and Firefox

## Development

### Running in Development Mode

The game is designed to run directly from the local server without any build process. Simply start the HTTP server and open in your browser.

### Debugging

In the browser console, you can access:
- `window.snakeCashRushSnapshot()`: Returns the current game state as JSON
- `window.snakeCashRushPlaceCashAhead()`: Spawns cash in front of the snake
- `window.snakeCashRushStep()`: Advances the game by one tick

### Modifying Game Settings

Edit these constants in `main.py` to customize gameplay:

```python
GRID_SIZE = 20              # Number of grid cells
BOARD_CELLS = 20            # Board dimensions
BOARD_PIXELS = 560          # Canvas size in pixels
BASE_TICK_MS = 160          # Initial game speed
MIN_TICK_MS = 82            # Maximum game speed
SPEED_STEP_MS = 5           # Speed increase per bill
SCORE_PER_BILL = 10         # Points awarded per bill
```

## Future Enhancements

Potential improvements for future versions:

- Leaderboard functionality
- Multiple difficulty levels
- Power-ups and special items
- Sound effects and background music
- Mobile touch controls
- Multiplayer mode
- Custom color themes

## Architecture Notes

- **Frontend-only**: The game runs entirely in the browser with no backend required
- **Python-powered**: Core game logic is implemented in Python using PyScript
- **JavaScript bridge**: Small JavaScript layer handles browser-specific operations like animation timing and localStorage
- **Responsive design**: Works on desktop and tablet devices

## License

This project is part of the GitHub Copilot Challenge.

## Support

For issues, questions, or feedback, please refer to the main project README or open an issue in the repository.

---

**Happy coding and enjoy the game!** 🎮💰