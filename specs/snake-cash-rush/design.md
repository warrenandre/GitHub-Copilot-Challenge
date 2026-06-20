# Design: Snake Cash Rush

## Technical Approach
Build a small web app under `games/snake/src` using HTML, CSS, and Python executed in the browser with PyScript. The game will use a single canvas for board rendering and standard DOM elements for the HUD, overlays, and control copy.

## Why This Approach
- The workspace is empty, so a no-build or near-zero-build solution reduces setup overhead and keeps delivery fast.
- PyScript lets the core gameplay logic stay in Python while still producing a browser-playable web app.
- Canvas provides crisp board rendering, easy animation accents, and predictable performance.
- DOM-based HUD elements keep the score keeper and overlays accessible and easy to style.

## Project Structure
- `games/snake/src/index.html`: application shell and HUD markup
- `games/snake/src/styles.css`: full visual system, layout, responsive behavior, and effects
- `games/snake/src/main.py`: game state, loop, rendering, input handling, score persistence
- `games/snake/src/app.js`: minimal browser interop glue if needed for canvas timing or DOM hooks
- `games/snake/README.md`: detailed getting started guide

## Core State Model
The runtime state will include:
- snake segments as an ordered list of grid coordinates
- current direction and pending direction
- money bill pickup coordinate
- current score
- best score from local storage
- running / game-over / ready state
- tick speed for progressive difficulty

## Game Loop
- Use a fixed-timestep loop driven by browser animation timing and elapsed-time accumulation.
- Advance game state only when the accumulated time exceeds the current tick interval.
- Re-render the board and HUD every frame for responsive feedback.

## Input Model
- Listen for arrow keys and `WASD`.
- Reject instant reversal into the opposite direction.
- Allow restart via keyboard and button.

## Fun and Visual Identity
- Replace standard pellets with stylized money bill pickups.
- Use a finance-inspired visual direction: dark glass surface, emerald accents, soft glow, and animated score feedback.
- Add small juice effects when collecting money, such as a pulse on the score panel and brief pickup burst visuals.
- Slightly increase game speed as score rises so the run becomes more exciting over time.

## Score Keeper
- Current score shown prominently in the HUD.
- Best score loaded from and saved to local storage.
- Best score updates immediately on surpassing the previous value.

## Responsive Strategy
- Center the game card within a modern full-screen layout.
- Scale the board visually for smaller screens while preserving square cells.
- Keep HUD readable in stacked layout on narrow viewports.

## Risks and Tradeoffs
- Python in the browser adds a runtime dependency and somewhat more setup weight than plain JavaScript, but it satisfies the requirement to use Python for the game.
- Canvas-only rendering for the board is simpler and smoother, but individual cell DOM nodes would be easier to inspect in tests. The chosen approach favors play feel and simpler rendering code.
- A lightweight browser-Python setup limits some module ergonomics, but it avoids introducing a separate backend for a compact game.
- Mobile touch controls are excluded from the initial scope unless requested, to keep the first version focused.

## Validation Strategy
- Manual gameplay validation for movement, collisions, scoring, and restart loop.
- Add small pure helper functions where practical so core logic such as collision and spawn validity can be checked deterministically if lightweight tests are added later.
- Validate the getting started guide by following the documented launch steps from a clean local run path.