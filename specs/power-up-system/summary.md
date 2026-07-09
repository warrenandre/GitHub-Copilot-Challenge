# Executive Summary — Power-Up System

> Builds on: [`intent.md`](./intent.md) · [`design.md`](./design.md) · [`tasks.md`](./tasks.md)

## Overview

The Power-Up System extends Snake Cash Rush with three collectible items — **Speed Boost**,
**Invincibility**, and **Double Points** — that grant the snake temporary abilities when collected.
Power-ups spawn on the board every three cash bills and expire after 100 ticks if ignored,
adding a risk/reward layer to the routing decisions players already make.

## Scope

### Included

- Three power-up types with unique visuals, durations, and mechanical effects
- Toroidal wall-wrap during Invincibility (enter left wall → exit right, and vice versa)
- HUD status text displaying the active effect name and tick countdown
- Data-driven `POWER_UP_CONFIG` dictionary enabling new types with a single-entry addition
- `snakeCashRushSnapshot()` updated to expose power-up state for DevTools inspection
- Full integration with the existing `reset_state` / restart flow

### Explicitly Out of Scope (v1)

- Multiple simultaneous power-ups on the board
- Stacking or chaining active effects
- Persistent power-up statistics or unlock progression
- Mobile / touch input changes
- Sound or haptic feedback
- Leaderboard metadata flags for doubled scores

## Approach

All logic is implemented in Python inside the `SnakeCashRush` class, consistent with the
project's architecture constraint that game state must not leak to module-level variables.
Two new frozen dataclasses (`PowerUpKind` enum, `PowerUp`) follow the same value-object
pattern as the existing `Point` type. Effect activation and deactivation are handled by three
focused methods (`activate_power_up`, `tick_active_power_up`, `deactivate_power_up`) that keep
the main `advance()` tick function readable. No new HTML elements, JS bridge methods, or CSS
classes are required — the feature uses the existing `status_text` DOM node for HUD feedback
and the Canvas 2D context for rendering.

## Key Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Emoji symbols render inconsistently across browsers | Medium | Low — cosmetic only | Add an ASCII fallback field to `POWER_UP_CONFIG` and test on Chrome, Firefox, and Safari before release |
| Speed Boost + natural speed increase interact unexpectedly | Medium | Medium — affects game feel | Save `tick_ms` at the moment of collection (post-natural-increase), not at game start; covered in Task 4 |
| Invincibility body-collision question (self vs wall only) | Low | Low | Acceptance criteria AC 3 explicitly states both wall and self-collision are skipped; confirm with playtester |
| Double Points inflates localStorage best score | Low | Low (no leaderboard yet) | Document in code comment; add metadata flag if a leaderboard is added in a future sprint |

## Estimated Effort

| Task | Description | Effort |
|------|-------------|--------|
| Task 1 | Types and constants | Small (< 1 hr) |
| Task 2 | `reset_state` attributes | Small (< 30 min) |
| Task 3 | Spawn + wrap helpers | Small (< 1 hr) |
| Task 4 | Activate / tick / deactivate lifecycle | Medium (1–2 hrs) |
| Task 5 | Wire into `advance()` | Medium (1–2 hrs) |
| Task 6 | Canvas rendering | Medium (1–2 hrs) |
| Task 7 | `snapshot_json` update | Small (< 30 min) |
| Task 8 | Manual playtesting | Medium (1–2 hrs) |
| **Total** | | **~6–10 hrs** |

## Success Metrics

| Metric | Target |
|--------|--------|
| All 10 acceptance criteria pass manual playtest | 10 / 10 |
| Power-up appears at the correct spawn interval | Every 3 bills |
| Each effect expires at the correct tick count | ±1 tick tolerance (fixed-timestep rounding) |
| Restarting clears all power-up state | 0 state bleed across runs |
| A 4th power-up type can be added in < 10 lines of code | Verified by adding a `SLOW_DOWN` type as a test |
| No regressions in existing cash-collection or scoring logic | Existing game play session scores match pre-feature baseline |
