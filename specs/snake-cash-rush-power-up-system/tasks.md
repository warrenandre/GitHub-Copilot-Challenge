# Tasks: Snake Cash Rush Power-Up System

## Implementation Plan

### T01 - Resolve Open Design Decisions and Lock Parameters
**Objective**
Finalize unresolved placeholders from design so implementation can proceed without hidden behavior changes.

**Deliverables**
- Decision log covering all placeholders from design (spawn cadence/chance, coexistence policy, stacking policy, same-type recollection behavior, durations, speed model, invincibility behavior scope, double-points scope, HUD wording/location, visual tokens, persistence policy).
- Confirmed parameter table for gameplay constants.
- Updated design notes if any assumption changes.

**Dependencies**
- `intent.md`
- `design.md`

**Definition of Done**
- Every `[DECISION REQUIRED]` item in design has an explicit decision, owner, and rationale.
- Approved parameter table exists and is ready to implement.

### T02 - Extend `SnakeCashRush` State Model
**Objective**
Add run-local power-up state in class fields while preserving encapsulation and baseline game behavior.

**Deliverables**
- New instance fields in reset/init paths:
  - `board_power_up`
  - `active_power_up_type`
  - `active_power_up_until_ms`
  - `run_clock_ms`
  - `next_spawn_check_ms`
- Tunable constants container for durations/spawn/speed settings.

**Dependencies**
- T01

**Definition of Done**
- No new global mutable state introduced.
- Restart/new run initializes all new fields deterministically.
- Existing movement controls/start flow remain unchanged.

### T03 - Implement Effect Timing Engine
**Objective**
Provide deterministic activation and automatic expiry using run-clock deadlines.

**Deliverables**
- `activate_power_up(power_up_type: str) -> None`
- `expire_power_up_if_needed() -> None`
- Derived effect accessors:
  - `current_score_award_for_cash() -> int`
  - `current_tick_ms() -> float`

**Dependencies**
- T02

**Definition of Done**
- Collecting a power-up sets active type and expiry timestamp.
- Active effect clears automatically at deadline.
- Baseline scoring is +10 and baseline movement timing returns after expiry.

### T04 - Implement Spawn Manager and Placement Rules
**Objective**
Spawn collectible power-ups on valid cells only, following approved cadence/chance policy.

**Deliverables**
- `maybe_spawn_power_up() -> None`
- `spawn_power_up(...) -> PowerUpPickup | None` helper (or equivalent)
- Occupancy validation against snake cells and cash cell.

**Dependencies**
- T01
- T02

**Definition of Done**
- Spawn checks run only during active gameplay.
- No spawn occurs on snake or cash cells.
- At most one board power-up exists at a time (unless T01 changes this policy).

### T05 - Integrate Collection, Collision, Scoring, and Speed Behavior
**Objective**
Connect power-up effects to the main `advance` flow without regressing existing rules.

**Deliverables**
- Power-up pickup detection and activation in movement step.
- Invincibility-aware collision branch.
- Cash scoring wired to `current_score_award_for_cash()`.
- Movement cadence wired to `current_tick_ms()`.

**Dependencies**
- T03
- T04

**Definition of Done**
- Speed boost temporarily accelerates movement and reverts.
- Invincibility suppresses configured death checks only during active window.
- Double points applies exactly to approved score events and reverts on expiry.
- No regression to start/restart/key input behavior.

### T06 - Add Power-Up Rendering and HUD Status
**Objective**
Expose active effect state clearly in the UI and make board pickups visually distinct.

**Deliverables**
- `draw_power_up(ctx)` integration into draw path.
- Distinct visual style per power-up type.
- HUD/status element integration using `powerUpStatus` with live remaining duration text.

**Dependencies**
- T04
- T05

**Definition of Done**
- Players can visually differentiate cash vs power-ups and each power-up type.
- HUD shows active effect + countdown while active and None/idle state otherwise.
- UI updates do not introduce perceptible frame stutter.

### T07 - Extend Debug Snapshot and Verification Surface
**Objective**
Support manual and automated verification of power-up runtime state.

**Deliverables**
- `snapshot_json()` fields:
  - `boardPowerUp`
  - `activePowerUpType`
  - `activePowerUpRemainingMs`
  - `isInvincible`
  - `scoreMultiplier`
  - `effectiveTickMs`
- Backward-compatible snapshot shape for existing consumers.

**Dependencies**
- T03
- T04
- T05

**Definition of Done**
- Snapshot reports correct values during idle, active, and expired states.
- Existing snapshot consumers continue to function.

### T08 - Ensure End-of-Run and Restart Cleanup
**Objective**
Guarantee power-up state clears correctly on game over and restart transitions.

**Deliverables**
- Cleanup hooks in end-game and restart paths.
- Reset behavior for active effects, deadlines, and board pickup state.

**Dependencies**
- T02
- T05

**Definition of Done**
- Game over immediately removes active effect behavior.
- Restart begins with no active power-up and no residual timers.

### T09 - Validate Acceptance Criteria and Performance
**Objective**
Confirm delivery against intent acceptance criteria and browser performance constraint.

**Deliverables**
- AC validation checklist mapped to AC1-AC5.
- Manual test matrix for spawn, pickup, expiry, restart, and HUD.
- Lightweight profiling notes for frame stability during active effects.

**Dependencies**
- T01
- T06
- T07
- T08

**Definition of Done**
- All acceptance criteria pass.
- No perceptible frame stutter observed on target browser setup.
- Known limitations and follow-ups are documented.
