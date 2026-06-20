# Tasks: Snake Cash Rush

## Phase 1: Project Skeleton
- Create the `games/snake/src` structure for the app.
- Add the base HTML shell, stylesheet, Python entrypoint, and any minimal browser interop file needed.
- Add a top-level game README with a detailed getting started guide.

## Phase 2: Core Gameplay
- Implement the board model, snake state, movement rules, and direction input.
- Implement money bill spawning in unoccupied cells.
- Implement collision detection for walls and self-impact.
- Implement game start, game-over, and restart flow.

## Phase 3: Score System
- Implement current score tracking.
- Implement best score persistence using browser local storage.
- Update HUD elements in response to game events.

## Phase 4: Visual Design and Fun Factor
- Apply a sleek modern layout and styling around the game board.
- Render the snake and money bill pickups with a distinct cash-themed look.
- Add collection feedback and progressive speed increase to make runs more exciting.
- Ensure the UI remains usable at smaller viewport widths.

## Phase 5: Validation
- Run the documented local startup flow to confirm the app launches.
- Validate movement, pickup growth, scoring, best-score persistence, collision handling, and restart behavior.
- Validate the getting started guide against the actual run steps.

## Phase 6: Final Handoff
- Record validation evidence.
- Assess documentation impact and keep the README aligned to the implementation.
- Prepare the stakeholder summary artifact and PDF if conversion tooling is available.

## Execution Notes
- Keep the first implementation frontend-only.
- Prefer simple local assets and direct browser APIs over added dependencies.
- Keep Python responsible for the core game logic, with only minimal JavaScript interop where required by the browser runtime.