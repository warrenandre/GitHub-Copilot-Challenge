# Phase 2 - Design

## Design Input
Source: Phase 1 intent for pause/resume with countdown.

## Architecture Overview
- Keep core state machine in Python (`SnakeCashRush` in `games/snake/src/main.py`).
- Keep browser utility bridge in JavaScript (`games/snake/src/app.js`) unchanged unless a browser primitive is required.
- Extend existing overlay/status patterns rather than introducing a new rendering layer.

## Component Changes

### 1. Game State Extensions (Python)
Add state flags:
- `paused: bool`
- `countdown_active: bool`
- `countdown_value: int`

State transitions:
- `running -> paused`
- `paused -> countdown_active -> running`
- `paused -> restart` (via existing restart path)

### 2. Input Handling
Extend `handle_keydown` in `main.py`:
- `P` toggles pause/resume.
- If `paused` and resume requested, trigger countdown.
- Ignore movement direction updates while paused/countdown except optional queueing policy.

Recommended policy:
- Ignore movement input while countdown is active to avoid race conditions.

### 3. HUD and Overlay Behavior
- Add a Pause/Resume button in HUD (HTML).
- Reuse overlay text area for countdown messaging (or add dedicated countdown label).
- Update status text values:
- Paused: "Paused. Press P or Resume to continue."
- Countdown: "Resuming in X..."
- Running: preserve current live-run messaging.

### 4. Game Loop Control
Current frame loop uses accumulator/tick stepping.
Changes:
- In `game_frame`, short-circuit simulation advancement when `paused` or `countdown_active`.
- Continue rendering so UI updates are visible.
- Keep `requestAnimationFrame` active for overlay/countdown updates.

### 5. Countdown Mechanism
Implement in Python using `window.setTimeout` callbacks:
- Initialize `countdown_value = 3`.
- Update UI each second to 3, 2, 1.
- At completion: set `paused = False`, `countdown_active = False`, restore running status.

### 6. Error Handling and Resilience
- Guard against repeated resume clicks while countdown is active.
- Ensure restart cancels any pending countdown callbacks to prevent late state mutation.
- Ensure pause is ignored when game is over or not yet started.

## Data Flow
1. User input (`P` or button click) -> `toggle_pause()`.
2. `toggle_pause()` updates state and UI.
3. On resume request -> `start_resume_countdown()`.
4. Countdown callback updates UI each second.
5. Countdown completion transitions back to `running`.
6. `game_frame` resumes `advance()` loop.

## Interfaces and Contracts
- New methods in `SnakeCashRush` (proposed):
- `toggle_pause()`
- `pause_game()`
- `resume_with_countdown()`
- `cancel_countdown()`
- Optional JS bridge additions are not required for this feature.

## Alternatives Considered
- Alternative A: Stop `requestAnimationFrame` entirely while paused.
- Rejected: makes countdown/UI updates less straightforward and increases restart edge cases.
- Alternative B: Implement countdown in JavaScript.
- Rejected: violates current architecture where gameplay state is Python-owned.

## Security and Observability Notes
- No new external dependencies.
- No sensitive data handling changes.
- Optional debug snapshot can include pause/countdown state for testability.

## Design-to-Acceptance Mapping
- AC1-AC3: State flags + game loop gating.
- AC4-AC5: Countdown mechanism and blocked simulation.
- AC6: Restart path compatibility and countdown cancellation.
- AC7: Status and overlay updates.
- AC8: Regression validation checklist.
