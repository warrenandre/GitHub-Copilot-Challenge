# Tasks — Power-Up System

## Task 1: Add data models (`PowerUpType` enum and `PowerUp` dataclass)

**Description**: Define the `PowerUpType` enum with `DOUBLE_POINTS` and `INVINCIBILITY` values, and a `PowerUp` frozen dataclass with `position: Point`, `kind: PowerUpType`, and `age_ms: float` fields.

**Deliverable**: New classes defined above `SnakeCashRush` in `main.py`.

**Dependencies**: None.

---

## Task 2: Add power-up constants

**Description**: Add module-level constants: `POWERUP_DURATION_MS = 6000.0`, `POWERUP_SPAWN_MIN_MS = 8000.0`, `POWERUP_SPAWN_MAX_MS = 15000.0`, `POWERUP_DESPAWN_MS = 10000.0`.

**Deliverable**: Constants added alongside existing game constants.

**Dependencies**: None.

---

## Task 3: Initialize power-up state in `reset_state()`

**Description**: Add instance attributes: `self.powerup = None`, `self.active_effect = None`, `self.effect_remaining_ms = 0.0`, `self.spawn_timer_ms = 0.0`, `self.next_spawn_delay_ms` (randomized between min/max).

**Deliverable**: Clean initial state on every game start/restart.

**Dependencies**: Tasks 1, 2.

---

## Task 4: Implement `spawn_powerup()` method

**Description**: Pick a random `PowerUpType`, find an unoccupied cell (not snake, not cash), create a `PowerUp` instance, and assign to `self.powerup`. Randomize `self.next_spawn_delay_ms` for the next cycle.

**Deliverable**: Power-ups appear on the board.

**Dependencies**: Tasks 1, 2, 3.

---

## Task 5: Add spawn timer logic in `game_frame()`

**Description**: Decrement `self.spawn_timer_ms` by `frame_delta`. When it reaches zero and no power-up is on the board, call `spawn_powerup()`. Also increment `powerup.age_ms` and despawn if it exceeds `POWERUP_DESPAWN_MS`.

**Deliverable**: Power-ups spawn and despawn on a timer.

**Dependencies**: Task 4.

---

## Task 6: Implement `collect_powerup()` method

**Description**: Set `self.active_effect` to the power-up's type, set `self.effect_remaining_ms = POWERUP_DURATION_MS`, clear `self.powerup` from the board, and reset spawn timer.

**Deliverable**: Collecting a power-up activates its effect.

**Dependencies**: Tasks 3, 4.

---

## Task 7: Detect power-up collision in `advance()`

**Description**: After computing `next_head`, check if `next_head == self.powerup.position`. If so, call `collect_powerup()`.

**Deliverable**: Snake can pick up power-ups by moving over them.

**Dependencies**: Task 6.

---

## Task 8: Apply "Double Points" effect in `advance()`

**Description**: When cash is collected, compute `multiplier = 2 if self.active_effect == PowerUpType.DOUBLE_POINTS else 1`. Multiply `SCORE_PER_BILL` by the multiplier.

**Deliverable**: Double points effect works during cash collection.

**Dependencies**: Task 6.

---

## Task 9: Apply "Invincibility" effect in `advance()`

**Description**: When checking body collision, skip the `end_game()` call if `self.active_effect == PowerUpType.INVINCIBILITY`. Wall collision remains fatal.

**Deliverable**: Snake passes through its own body while invincible.

**Dependencies**: Task 6.

---

## Task 10: Implement `expire_effect()` and countdown in `game_frame()`

**Description**: Decrement `self.effect_remaining_ms` by `frame_delta` each frame. When it reaches zero, set `self.active_effect = None` and `self.effect_remaining_ms = 0.0`.

**Deliverable**: Effects automatically expire after 6 seconds.

**Dependencies**: Task 6.

---

## Task 11: Implement `draw_powerup(ctx)` method

**Description**: Render the power-up as a distinct shape/icon per type — e.g. a gold diamond for double points, a cyan shield for invincibility. Use glow effects similar to existing cash rendering.

**Deliverable**: Power-ups are visually distinguishable from cash bills.

**Dependencies**: Task 4.

---

## Task 12: Implement `get_snake_color()` and `draw_effect_bar(ctx)`

**Description**: `get_snake_color()` returns gold (`#ffd700`) for double points, cyan (`#00e5ff`) for invincibility, or default green. `draw_effect_bar()` draws a horizontal bar at the top of the canvas showing `effect_remaining_ms / POWERUP_DURATION_MS` as a percentage, colored to match the effect.

**Deliverable**: Players see what effect is active and how long it lasts.

**Dependencies**: Task 10.

---

## Task 13: Update `snapshot_json()` with power-up state

**Description**: Add `powerup` (position + kind or null), `activeEffect` (string or null), and `effectRemainingMs` (float) to the JSON payload.

**Deliverable**: Debug helper exposes full power-up state for testing.

**Dependencies**: Tasks 3, 6.
