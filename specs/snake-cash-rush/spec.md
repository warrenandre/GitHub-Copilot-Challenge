# Specification: Snake Cash Rush

## Scope
Build a browser-based Snake game under `games/snake/src` with Python-driven game logic, a money-bill collection theme, sleek modern UI, current score display, persisted best score, and a detailed getting started guide.

## Functional Requirements
1. The app shall render a playable Snake game in the browser without requiring a backend service.
2. The snake shall move continuously on a visible game board once the game starts.
3. The player shall control the snake with keyboard input.
4. The snake shall grow by one segment when it collects a money bill pickup.
5. The app shall increase the score when a money bill is collected.
6. The app shall display the current score during active play.
7. The app shall display a best score and preserve it across browser refreshes using local storage.
8. The game shall end when the snake collides with a wall or with itself.
9. The player shall be able to restart the game without reloading the page.
10. The app shall present a polished modern interface around the board, including a clear title, score panel, call-to-action, and visual feedback for game states.
11. Money bill pickups shall be visually distinct from the snake and board background.
12. The UI shall adapt cleanly to common desktop and narrow mobile viewport widths.
13. The primary game logic shall be implemented in Python.
14. The project shall include a detailed getting started guide covering prerequisites, local run steps, and how to play.

## Gameplay Enhancements
1. The game shall include at least one distinctive fun factor beyond plain Snake, implemented through visual effects, speed ramping, or feedback styling.
2. Score progression shall feel rewarding, with immediate visual feedback when money bills are collected.
3. The start and game-over states shall be clearly communicated in the interface.

## Non-Functional Requirements
1. The game loop shall feel responsive and visually smooth on a modern desktop browser.
2. The code shall remain simple enough to maintain in a small frontend-only project structure.
3. The implementation shall keep assets inline or local so the game can run directly from the workspace.

## Acceptance Criteria
1. On load, the page shows the game title, board, current score, best score, and a way to start or restart play.
2. When the player presses a valid movement key, the snake moves in that direction and continues moving automatically.
3. When the snake eats a money bill, the snake length increases, the score increases, and a new money bill appears in a free board cell.
4. The best score updates only when the current score exceeds the stored best score and remains visible after reload.
5. When the snake hits a wall or itself, movement stops, a game-over state appears, and the player can start a new run.
6. The game is implemented inside `games/snake/src`.
7. The interface looks intentionally modern rather than default browser styling, using a cohesive visual system.
8. The layout remains usable at small viewport widths without overlapping critical UI.
9. The getting started guide is sufficient for a new developer to run the game locally without guessing missing steps.

## Test Focus Areas
- Direction change validation, including prevention of illegal instant reversal.
- Collision detection with walls and snake body.
- Pickup spawning only in unoccupied cells.
- Score increments and best score persistence.
- Restart behavior fully resetting transient game state.
- UI state transitions for start, active play, and game over.