# Intent: Snake Cash Rush Power-Up System

## Goal
Add a power-up system to Snake Cash Rush where players can collect temporary ability items (speed boost, invincibility, double points) to create more strategic, varied runs without breaking core snake gameplay.

## Problem Statement
The current game loop has one pickup type (cash) and one progression path (higher score with increasing speed). This makes runs predictable and limits player choice. A power-up system should introduce short-lived tactical decisions and high-impact moments while preserving the game's clarity and responsiveness.

## Target Users
- Primary: Players currently playing Snake Cash Rush in the browser.
- Secondary: Maintainers/developers who will extend or balance gameplay in future challenges.

## Constraints
- Runtime/environment: Browser-based PyScript/Pyodide game; no server dependency for gameplay behavior.
- Architecture: Mutable gameplay state remains encapsulated in `SnakeCashRush`; avoid introducing global mutable state.
- Compatibility: Keep current movement controls and restart behavior unchanged.
- Performance: No perceptible frame stutter during active effects on typical modern desktop browsers.
- UX clarity: Active power-up effect and remaining duration must be visible to the player.
- Scoring baseline: Existing cash scoring (+10) remains the default when no multiplier effect is active.

Assumptions (until clarified):
- Exactly three initial power-up types are in scope for this feature: speed boost, invincibility, and double points.
- Power-ups are temporary and expire automatically after a defined duration.
- Power-ups are collectibles on the board (not button-triggered abilities).

## Acceptance Criteria
- Power-up generation:
  - The game can spawn collectible power-up items on valid, unoccupied board cells during an active run.
  - Spawned power-ups are visually distinguishable from cash and from each other.
- Effect activation:
  - Collecting a speed boost applies a faster movement state for a temporary duration, then automatically returns to the pre-effect speed behavior.
  - Collecting invincibility prevents death from wall and self collisions for a temporary duration; after expiry, normal collision rules are restored.
  - Collecting double points makes each cash pickup award 2x points for a temporary duration; after expiry, cash returns to +10 points.
- Effect visibility:
  - The HUD or status area shows the currently active power-up and a live countdown/remaining duration while active.
- State transitions:
  - Restarting or game over clears all active power-up effects and related timers/state.
  - Power-up behavior does not break existing start/restart/key input flows.
- Testability/debug support:
  - Game state snapshot/debug helpers expose enough fields to verify active power-up type and remaining duration in automated/manual checks.

## Open Questions
- Spawn rules:
  - What is the exact spawn cadence/chance for power-ups (time-based, score-based, or random per tick)?
  - Can cash and power-ups coexist simultaneously on different cells?
- Stacking rules:
  - Can multiple power-ups be active at the same time?
  - If same-type power-up is collected while active, should duration refresh, extend, or be ignored?
- Balancing:
  - What exact duration should each power-up use?
  - Should speed boost be a fixed multiplier, a fixed tick reduction, or override current scaling logic?
- Invincibility behavior:
  - During invincibility, should collisions pass through obstacles, bounce, or clip without ending the game?
  - Should invincibility affect only death checks, or also interaction with score/speed progression?
- Scoring behavior:
  - Should double points apply only to cash pickups or also any future score events?
- UX details:
  - Where should active-effect UI appear (status text, HUD badge, overlay area)?
  - What visual language should represent each power-up on canvas?
- Persistence/debug:
  - Should power-up stats be tracked across runs (best streaks, pickups collected), or run-local only?
