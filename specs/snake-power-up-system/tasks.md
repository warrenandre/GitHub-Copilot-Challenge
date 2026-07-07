# Tasks

## Task 1 - Finalize Gameplay Rules and Constants

### Objective
Lock gameplay decisions that were assumptions in design so implementation is deterministic.

### Deliverables
- Confirmed constants for:
  - Power-up durations (speed boost, invincibility, double points)
  - Spawn interval window
  - Speed boost modifier and safe tick floor
- Confirmed policies for:
  - One board power-up at a time
  - Refresh-not-stack for same-type pickup
  - Invincibility collision handling
  - Double-points scope
- A constants section in code (or config block in class) documenting chosen values.

### Completion Criteria
- All gameplay-policy placeholders removed from implementation plan.
- Chosen values are reflected in code-ready constants and test expectations.

## Task 2 - Add Power-Up Data Model and State Fields

### Objective
Extend SnakeCashRush state to track board power-ups and active timed effects.

### Deliverables
- New in-class model/type for power-up entity (type, position, spawn time, ttl).
- New SnakeCashRush fields:
  - current_power_up
  - active_effects
  - next_power_up_spawn_at_ms
  - base_tick_ms (if separated from dynamic tick)
- Reset/start lifecycle updates so new fields initialize correctly.

### Completion Criteria
- No global mutable game state introduced.
- Game can still start/restart without power-up errors.

## Task 3 - Implement Spawn Scheduling and Placement

### Objective
Spawn power-ups at valid times and valid board cells.

### Deliverables
- Spawn scheduler logic (due-time check + next spawn scheduling).
- Placement logic that excludes:
  - snake body cells
  - cash cell
  - out-of-board cells
- Random power-up type selection from the three supported effects.

### Completion Criteria
- At most one power-up exists on board at once.
- Power-up spawns repeatedly over time during active gameplay.

## Task 4 - Implement Pickup Detection and Effect Activation

### Objective
Detect when snake collects a power-up and activate/refresh effect timers.

### Deliverables
- Pickup collision check against snake head movement.
- Activation handler that writes/refreshes expiration timestamps in active_effects.
- Post-pickup cleanup:
  - remove board power-up
  - schedule next spawn

### Completion Criteria
- Collecting a power-up consistently activates the correct effect.
- Re-collecting same type refreshes duration (per policy).

## Task 5 - Integrate Effect Engine into Game Tick Rules

### Objective
Apply active effects to movement speed, collision outcome, and scoring.

### Deliverables
- Expiry pruning each tick/frame based on current timestamp.
- Speed boost integration into effective tick interval.
- Invincibility integration into collision death branch.
- Double-points multiplier applied on cash score events.

### Completion Criteria
- Effects start and expire deterministically.
- Baseline behavior returns immediately after expiry.
- No freeze/skip regressions in game loop timing.

## Task 6 - Add HUD and Visual Feedback

### Objective
Make active effects and remaining durations visible to players.

### Deliverables
- UI element(s) for active power-ups status in HUD.
- Rendering updates for:
  - spawned power-up item on board
  - active effect labels and countdowns
- Optional styling updates for readability and distinction by effect type.

### Completion Criteria
- Players can identify active effects at a glance.
- Remaining duration is visible or clearly inferable.

## Task 7 - Preserve Compatibility and Regression Safety

### Objective
Ensure existing game flows remain stable with new mechanics.

### Deliverables
- Validation checklist for:
  - start run
  - restart via button and R key
  - game over and overlay behavior
  - best score persistence behavior
- Guardrails for edge cases:
  - effect expiry on same tick as collision
  - pickup near wall/body
  - restart while effects are active

### Completion Criteria
- Existing non-power-up gameplay works as before when no effects are active.
- No broken flow in restart/game-over transitions.

## Task 8 - Add Tests and Verification Scenarios

### Objective
Create deterministic checks for power-up lifecycle and rule interactions.

### Deliverables
- Unit/logic tests (or deterministic harness checks) for:
  - spawn validity and scheduling
  - pickup and activation
  - timer expiry behavior
  - speed boost timing effect
  - invincibility collision behavior
  - double-points score multiplication
- Manual smoke-test checklist for browser playthrough.

### Completion Criteria
- Acceptance criteria from intent are covered by explicit test cases/checklist items.
- Test evidence demonstrates pass/fail outcomes.

## Task 9 - Documentation Updates

### Objective
Document player-facing and maintainer-facing behavior.

### Deliverables
- Update gameplay docs with:
  - power-up types and effects
  - duration behavior
  - HUD interpretation
- Update developer notes with:
  - state ownership in SnakeCashRush
  - key methods added/updated
  - extension guidance for future power-up types

### Completion Criteria
- README/docs reflect current feature behavior.
- New contributors can locate power-up architecture quickly.

## Execution Order
1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7
8. Task 8
9. Task 9

## Traceability Matrix
- Intent AC1 (spawn/pickup): Tasks 3, 4, 8
- Intent AC2 (three effects): Tasks 2, 5, 8
- Intent AC3 (timing lifecycle): Tasks 4, 5, 8
- Intent AC4 (rules interaction): Tasks 5, 8
- Intent AC5 (UI feedback): Task 6
- Intent AC6 (stability): Task 7
