# Snake Cash Rush

A modern, browser-based reimagining of the classic Snake game, featuring cash-bill pickups, smooth animations, live score tracking, and persistent best-score storage. The game logic is powered by Python running through PyScript, while the UI is built with vanilla HTML, CSS, and JavaScript.

**Theme:** Arcade Finance — Chase stacks, build momentum, and beat your best run.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [How to Play](#how-to-play)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10** or later installed on your local machine
- A modern web browser (Chrome, Edge, Firefox, Safari)
- Internet access on first load (PyScript runtime and Google Fonts are fetched from CDNs)
- Git (optional, for cloning the repository)

### Installation & Running

1. Navigate to the project directory:

   ```powershell
   cd games\snake
   ```

2. Start a local Python HTTP server:

   ```powershell
   python -m http.server 8000
   ```

3. Open your browser and navigate to:

   ```
   http://localhost:8000/src/
   ```

4. Wait 2-3 seconds for the PyScript runtime to initialize (first load may take longer).

5. Click **"Play Now"** or press any arrow key to start the game.

---

## 🎮 How to Play

### Objective
Collect cash bills to grow your snake and increase your score while avoiding collisions with walls and your own body.

### Controls

| Input | Action |
|-------|--------|
| **Arrow Keys** | Move snake (up, down, left, right) |
| **W, A, S, D** | Alternative movement controls |
| **R** | Restart the current run anytime |

### Gameplay Mechanics

- **Score**: Each cash bill collected grants **+10 points**
- **Speed**: Your snake gradually accelerates as you collect more bills (maximum speed reached at 10+ bills)
- **Grid**: The game board is a 20×20 grid with a visual cell size of 28 pixels
- **Best Score**: Your highest score is automatically saved in browser local storage and persists across sessions

### Game Over Conditions

- **Wall Collision**: Snake head touches the board boundary
- **Self Collision**: Snake head touches any part of its own body

---

## 📁 Project Structure

```
games/snake/
├── README.md           # This file — documentation and guides
├── src/
│   ├── index.html      # Application shell, HUD, canvas, and UI overlay
│   ├── styles.css      # Visual design, layout, animations, and responsive styling
│   ├── main.py         # Core game logic, physics, and rendering (Python/PyScript)
│   └── app.js          # Lightweight browser bridge for animation and storage
└── (other project files)
```

### File Descriptions

#### `index.html`
- Defines the HTML structure of the application
- Includes the game canvas and HUD elements (score, best score, buttons)
- Loads PyScript runtime, Google Fonts, and stylesheets from CDNs
- Contains the overlay UI for initial state and end-game states

#### `styles.css`
- Modern, responsive design using CSS Grid and Flexbox
- Gradient backgrounds, animated orb effects, and smooth transitions
- Responsive layout that adapts to different screen sizes
- Sleek typography with Space Grotesk and Sora fonts from Google Fonts

#### `main.py`
- **Game Engine**: Tick-based game loop with configurable frame timing
- **Data Models**: `Point` dataclass for position tracking
- **Game State**: Manages snake position, cash bill locations, score, and best score
- **Rendering**: Draws grid, snake, and cash bills to the canvas
- **Physics**: Collision detection, boundary checking, and smooth movement
- **PyScript Integration**: Interfaces with browser DOM and JavaScript bridge via `js` module

**Key Constants:**
- `GRID_SIZE`: 20 cells per dimension
- `BOARD_PIXELS`: 560×560 pixel canvas (28 pixels per cell)
- `BASE_TICK_MS`: Initial game speed (160ms per tick)
- `MIN_TICK_MS`: Fastest game speed (82ms per tick)
- `SCORE_PER_BILL`: Points awarded for each cash bill (10)

#### `app.js`
- **Animation Bridge**: Provides `requestAnimationFrame` wrapper for smooth rendering
- **Storage Bridge**: Wraps browser `localStorage` for persistent score storage
- **Minimal Design**: Keeps JavaScript footprint small; defers all logic to Python

---

## 💻 Development

### Architecture Overview

1. **Frontend Layer** (`index.html`, `styles.css`)
   - User interface and visual design
   - Event handlers for keyboard input and button clicks

2. **Game Logic** (`main.py`)
   - Runs in the browser via PyScript (Python compiled to WebAssembly)
   - Handles all game state, physics, and rendering
   - Communicates with DOM through PyScript's `js` module

3. **Browser Bridge** (`app.js`)
   - Minimal glue code between Python and JavaScript APIs
   - Handles animation frame scheduling and local storage operations

### Why This Architecture?

- **Performance**: Python's logic runs as WebAssembly, offloading computation from the main JavaScript thread
- **Maintainability**: Game logic is cleanly separated from UI concerns
- **Simplicity**: No backend server required; runs entirely in the browser
- **Portability**: Can be deployed anywhere static files are served

### Local Development Tips

- The game requires a local server (not `file://` URLs) due to PyScript module imports and CORS policies
- Browser developer console is useful for debugging (F12 or Cmd+Option+I)
- First load may be slow due to PyScript runtime initialization and CDN downloads
- Clear browser cache if styling or PyScript assets appear out of date

---

## 🔧 Troubleshooting

### The page opens but the game doesn't start

**Solution:**
- Ensure you're accessing the game via `http://localhost:8000/src/` and not by directly opening the HTML file
- Check the browser's developer console (F12 → Console tab) for errors
- Look for failed network requests to PyScript CDN assets (likely a connectivity issue)

**Prevention:**
- Always use the `http://` protocol when running the local server
- Verify your firewall isn't blocking localhost connections

---

### Styling looks broken or fonts aren't loading

**Solution:**
- Confirm you have active internet access (fonts and stylesheets load from external CDNs)
- Refresh the page (Ctrl+R or Cmd+R)
- Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

**Prevention:**
- Keep your internet connection active during development
- Use a modern browser with strong CSS Grid/Flexbox support

---

### Best score doesn't persist or resets unexpectedly

**Solution:**
- Verify that local storage is enabled in your browser settings
- Avoid private/incognito browsing mode (local storage is typically cleared when the session ends)
- Check browser developer console for storage-related errors

**Prevention:**
- Use normal browsing mode for development and testing
- Check browser privacy settings if running in a corporate or restricted environment

---

### PyScript takes a long time to load

**Solution:**
- This is normal on the first load (PyScript runtime is downloaded and cached)
- Subsequent loads should be faster due to browser caching
- Check your internet connection speed
- Try a different browser if the issue persists

**Prevention:**
- Ensure a stable internet connection for the initial load
- Use a browser with good performance for WebAssembly (Chrome, Edge, or Firefox recommended)

---

## 📝 Additional Notes

- **No Backend Required**: The entire application runs client-side; no server-side code is needed
- **Cross-Platform**: Works on Windows, macOS, and Linux with Python 3.10+
- **Future Enhancements**: Could include multiplayer leaderboards, power-ups, difficulty levels, or mobile touch controls
- **Accessibility**: Game canvas includes ARIA labels for screen reader compatibility

---

## 🎯 Credits & Inspiration

Built as part of the GitHub Copilot Enterprise Challenge to demonstrate production-ready web development practices using modern tools and languages.