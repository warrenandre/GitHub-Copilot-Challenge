# Intent — Power-Up System

## Goal

Add a **power-up system** to Snake Cash Rush that spawns special collectible items on the board
alongside the regular cash bill. When the snake collects a power-up, it gains a temporary ability
for a fixed duration. Three initial ability types — Speed Boost, Invincibility, and Double Points —
add strategic variety and raise the skill ceiling by rewarding players who actively route toward
beneficial pickups.

## Problem Statement

Currently the only collectible is the cash bill, which always grants the same reward (+10 points,
one segment of growth, and a small tick-speed increase). After a few runs the gameplay loop becomes
predictable and lacks moments of escalation or recovery. Without power-ups there is no way for a
player to intentionally trade risk for a temporary advantage, and no mechanic to create memorable
"clutch" moments. This limits long-term engagement.

## Target Users

- **Casual browser players** who want variety and short bursts of excitement in a single run.
- **Score-chasers** who will learn power-up timing to maximise the Double Points window.
- **Developers** extending the game — the system should be easy to add new power-up types to.

## Constraints

### Technical
- All game logic must remain in **Python 3.10+** running via **PyScript 2025.3.1** in-browser.
- No new external dependencies, build tools, or bundlers may be introduced.
- DOM and timer interactions must continue to go through the existing `window.snakeCashRushBridge`
  or `window.setTimeout` via `create_proxy()` — direct `window.*` calls from Python are not allowed.
- Power-up state must live **inside `SnakeCashRush`** — no module-level mutable variables.
- The `Point` frozen dataclass is the canonical grid-coordinate type; power-up positions must use it.
- The fixed-timestep accumulator game loop must not be altered.
- The canvas is 560 × 560 px on a 20 × 20 cell grid; power-up rendering must respect these constants.

### Non-functional
- A power-up must not appear on a cell already occupied by the snake or the cash bill.
- Power-up duration is purely tick-based (not wall-clock) so it scales correctly with player speed.
- At most **one power-up** is active on the board at any time in the initial implementation.
- Each power-up type must be visually distinct from the cash bill and from each other.
- The active power-up type and remaining duration must be visible in the HUD or on the board.

### Out of Scope
- Stacking multiple simultaneous power-ups.
- Persistent power-up statistics or unlock systems.
- Mobile / touch controls.
- Sound effects.
- Power-ups that affect the board layout (e.g. adding walls).

## Acceptance Criteria

1. A power-up item appears on the board at a random empty cell after a configurable number of cash
   bills have been collected (default: every 3 bills), and disappears after a configurable number
   of ticks if not collected (default: 100 ticks).
2. Collecting a **Speed Boost** power-up reduces `tick_ms` by an additional 20 ms (floored at
   `MIN_TICK_MS`) for 50 ticks, then restores the pre-boost tick speed.
3. Collecting an **Invincibility** power-up causes wall and self-collision checks to be skipped for
   30 ticks, then restores normal collision behaviour. The snake must wrap around walls during this
   window (entering the left wall exits from the right, etc.).
4. Collecting a **Double Points** power-up causes every cash bill collected during the next 40 ticks
   to award `SCORE_PER_BILL * 2` points instead of `SCORE_PER_BILL`.
5. Each power-up type is rendered with a unique colour and symbol on the canvas, clearly different
   from the green cash bill.
6. The HUD displays the active power-up name and a tick-countdown while an effect is in progress.
7. Power-up state is included in the `snakeCashRushSnapshot()` JSON output.
8. Restarting the game (`R` key or Restart button) clears all active power-up state immediately.
9. The best score saved to `localStorage` correctly accounts for doubled points.
10. A new developer can add a fourth power-up type by adding one entry to a data structure without
    modifying game-loop or rendering logic.
