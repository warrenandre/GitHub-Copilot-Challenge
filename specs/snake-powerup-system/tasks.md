# Tasks: Snake Power-Up System

## Delivery Order
Work flows from the inside out: data model first, then game logic, then rendering, then HUD,
then polish. Each task has no dependencies except those listed, so a single engineer can work
top-to-bottom. Tasks 1–2 are prerequisite for all later tasks; Tasks 3–6 can proceed in
parallel after Task 2 is complete.

---

## Task List

### Task 1: Add module-level constants and `PowerUp` dataclass
- **Deliverable**: `main.py` contains the `PowerUp` frozen dataclass and all new module-level
  constants (`POWERUP_SPEED`, `POWERUP_INVINCIBILITY`, `POWERUP_DOUBLE`, `POWERUP_KINDS`,
  `POWERUP_SPAWN_INTERVAL_TICKS`, `POWERUP_DESPAWN_TICKS`, `SPEED_BOOST_TICKS`,
  `SPEED_BOOST_FACTOR`, `INVINCIBILITY_TICKS`, `DOUBLE_POINTS_TICKS`).
- **Depends on**: None
- **Effort estimate**: XS — pure data declarations, no logic, ~25 lines.
- **Acceptance criteria**:
  - `PowerUp(kind=POWERUP_SPEED, position=Point(1, 1))` is constructable and frozen.
  - All constants are defined at module scope with `UPPER_SNAKE_CASE` names.
  - No existing constants are modified.

### Task 2: Extend `reset_state()` with power-up state initialisation
- **Deliverable**: `reset_state()` initialises all six new instance fields:
  `powerup`, `active_effect`, `effect_ticks_remaining`, `powerup_despawn_ticks`,
  `next_powerup_ticks`, `pre_boost_tick_ms`.
- **Depends on**: Task 1
- **Effort estimate**: XS — six one-line assignments inside an existing method.
- **Acceptance criteria**:
  - After `reset_state()`, `self.powerup is None`, `self.active_effect is None`,
    `self.effect_ticks_remaining == 0`, `self.next_powerup_ticks == POWERUP_SPAWN_INTERVAL_TICKS`.
  - Restart during an active power-up effect clears the effect (verified manually by
    collecting a power-up mid-game then restarting).

### Task 3: Implement `spawn_powerup()`
- **Deliverable**: New `spawn_powerup(self, snake: list[Point], cash: Point) -> PowerUp | None`
  method that selects a random free cell (not overlapping snake or cash bill) and a random
  kind from `POWERUP_KINDS`.
- **Depends on**: Task 1
- **Effort estimate**: S — mirrors the existing `spawn_cash()` implementation with an extra
  exclusion for the cash position and a random kind selection, ~20 lines.
- **Acceptance criteria**:
  - Returned `PowerUp.position` is never equal to any snake segment or the cash position.
  - All three kinds appear across repeated calls (probabilistic).
  - Returns `None` only when the board has no free cells (not reachable in normal play).

### Task 4: Implement `apply_effect()` and `expire_effect()`
- **Deliverable**: Two new methods that activate and deactivate a power-up effect with correct
  state mutation.
  - `apply_effect(kind: str) -> None`: calls `expire_effect()` if already active, then
    sets `active_effect`, `effect_ticks_remaining`, and — for Speed Boost — saves
    `pre_boost_tick_ms` and reduces `tick_ms`.
  - `expire_effect() -> None`: restores `tick_ms` if Speed Boost was active, then clears
    `active_effect` and `effect_ticks_remaining`.
- **Depends on**: Tasks 1, 2
- **Effort estimate**: S — straightforward conditional state mutations, ~35 lines.
- **Acceptance criteria**:
  - Collecting Speed Boost reduces `tick_ms` by `SPEED_BOOST_FACTOR`; expiry restores the
    exact pre-boost value (not `BASE_TICK_MS`).
  - Calling `apply_effect()` while an effect is running correctly replaces it (old state
    fully cleared before new state is set).
  - `expire_effect()` is a no-op when `active_effect is None`.

### Task 5: Modify `advance()` to integrate power-up lifecycle
- **Deliverable**: `advance()` handles all six tick-by-tick power-up operations described in
  the design (effect countdown, wall-wrap invincibility, power-up collection, score modifier,
  despawn countdown, spawn countdown) and calls `update_powerup_hud()`.
- **Depends on**: Tasks 2, 3, 4
- **Effort estimate**: M — the most complex task; touches the core game loop and must not
  regress existing cash collection, score, speed progression, or collision logic. ~60 lines of
  new/modified code with careful ordering.
- **Acceptance criteria (maps to intent.md criteria 3–11)**:
  - AC 3: Collecting a power-up calls `apply_effect()` immediately.
  - AC 4: Speed Boost reduces `tick_ms`; restores on expiry.
  - AC 5: Invincibility wraps the snake at walls; self-collision move is allowed.
  - AC 6: Double Points awards `SCORE_PER_BILL * 2` per bill while active.
  - AC 7: At most one power-up is on the board at any time.
  - AC 9: Power-ups despawn after `POWERUP_DESPAWN_TICKS` ticks if uncollected.
  - AC 10: A new power-up spawns every `POWERUP_SPAWN_INTERVAL_TICKS` ticks (no power-up
    if one is already present).
  - AC 11: All state resets correctly via `reset_state()` (tested by restart mid-effect).
  - Existing cash collection, score increments, and speed progression are unaffected when
    no power-up is active.

### Task 6: Implement `draw_powerup()` and update `draw()`
- **Deliverable**: `draw_powerup(ctx)` renders the on-board power-up item using a
  kind-specific background colour and glyph. `draw()` calls `draw_powerup(ctx)` between
  `draw_cash()` and `draw_snake()`.
- **Depends on**: Task 1
- **Effort estimate**: S — canvas drawing, follows the pattern of the existing `draw_cash()`
  and `draw_snake()` methods, ~30 lines.
- **Acceptance criteria (maps to AC 12)**:
  - Speed Boost item renders in amber (`#f59e0b`) with `⚡` glyph.
  - Invincibility item renders in violet (`#a78bfa`) with `🛡` glyph.
  - Double Points item renders in rose (`#f43f5e`) with `✕2` glyph.
  - Power-up item is visually distinct from cash bills.
  - `draw_powerup()` is a no-op (no canvas change) when `self.powerup is None`.

### Task 7: Add `#powerupIndicator` HUD element and implement `update_powerup_hud()`
- **Deliverable**:
  - `index.html`: new `<div id="powerupIndicator">` element in the HUD area.
  - `styles.css`: styles for `.powerup-indicator` (hidden by default, `visible` class shows
    it), plus per-kind colour modifier classes (`.powerup-speed`, `.powerup-invincibility`,
    `.powerup-double`).
  - `main.py`: `__init__` acquires the DOM reference; `update_powerup_hud()` updates text
    content and CSS classes to reflect `active_effect` and `effect_ticks_remaining`.
- **Depends on**: Tasks 4, 5
- **Effort estimate**: S — DOM wiring and CSS, ~40 lines across three files.
- **Acceptance criteria (maps to AC 8)**:
  - HUD indicator is hidden when no effect is active.
  - HUD shows the correct effect name and tick count while an effect is running.
  - HUD updates every tick (not every frame).
  - Indicator colour matches the kind (amber / violet / rose).

### Task 8: Cross-browser smoke test and final polish
- **Deliverable**: All twelve acceptance criteria from `intent.md` are verified manually in a
  Chromium-based browser. Any visual inconsistencies in the HUD or canvas rendering are fixed.
- **Depends on**: Tasks 5, 6, 7
- **Effort estimate**: S — manual verification against the AC checklist, minor CSS/copy tweaks.
- **Acceptance criteria**:
  - All 12 ACs from `intent.md` pass in a Chromium browser.
  - No console errors during normal play.
  - Restart during an active effect produces a clean state with no visible artefacts.
  - Game-over overlay message is unaffected by power-up state.
